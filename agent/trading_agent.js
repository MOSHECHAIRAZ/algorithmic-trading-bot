// trading_agent.js (גרסה 5, סנכרון עם התיק האמיתי)
require('dotenv').config();
const { IBApi, EventName, Stock } = require('@stoqey/ib');
const axios = require('axios');
const cron = require('node-cron');
const fs = require('fs');
const path = require('path');
const winston = require('winston');
const { setState, getState } = require('./state_manager');
const util = require('util');

// --- הגדרות ---
const CONFIG = (() => {
    try {
        const config = JSON.parse(fs.readFileSync(path.join(__dirname, '../system_config.json'), 'utf-8'));
        return {
            modelApiUrl: `http://${config.api_settings?.host || 'localhost'}:${config.api_settings?.port || 5000}`,
            logFile: path.join(__dirname, 'trading_log.txt'),
            ib: {
                host: config.ibkr_settings?.host || '127.0.0.1',
                port: parseInt(config.ibkr_settings?.port || '4001', 10),
                clientId: parseInt(config.ibkr_settings?.clientId || '101', 10),
            },
            agent: config.agent_settings || { TEST_MODE_ENABLED: false, TEST_BUY_QUANTITY: 1, TEST_BUY_PRICE_FACTOR: 0.95 },
            contract: config.contract || {}
        };
    } catch (e) {
        console.error('Failed to load system config, using defaults:', e.message);
        return {
            modelApiUrl: 'http://localhost:5000',
            logFile: path.join(__dirname, 'trading_log.txt'),
            ib: { host: '127.0.0.1', port: 4001, clientId: 101 },
            agent: { TEST_MODE_ENABLED: false, TEST_BUY_QUANTITY: 1, TEST_BUY_PRICE_FACTOR: 0.95 },
            contract: {}
        };
    }
})();

const ib = new IBApi({ host: CONFIG.ib.host, port: CONFIG.ib.port, clientId: CONFIG.ib.clientId, show_raw_messages: false });
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }), winston.format.printf(i => `[${i.timestamp}] [${i.level.toUpperCase()}] ${i.message}`)),
    transports: [new winston.transports.Console(), new winston.transports.File({ filename: CONFIG.logFile })]
});

const log = (message, level = 'info') => logger.log({ level, message });

// --- מאזינים גלובליים לעדכוני פקודות ---
// --- ניהול מצב בזמן אמת על בסיס orderStatus ---
ib.on(EventName.openOrder, (orderId, contract, order, orderState) => {
    log(`[TWS] openOrder: OrderId=${orderId}, Symbol=${contract.symbol}, Action=${order.action}, Qty=${order.totalQuantity}, Status=${orderState.status}`);
});

ib.on(EventName.orderStatus, async (orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice) => {
    log(`[TWS] orderStatus: OrderId=${orderId}, Status=${status}, Filled=${filled}, Remaining=${remaining}, AvgFillPrice=${avgFillPrice}`);
    try {
        // נטפל רק בפקודות שבוצעו (Filled)
        if (status === 'Filled') {
            let state = await getState('trade_state') || {};
            // נזהה האם זו פקודת כניסה או יציאה (TP/SL)
            // אם יש parentOrderId במצב, נשתמש בו לזיהוי משפחת הפקודות
            if (state.parentOrderId && (orderId == state.parentOrderId || parentId == state.parentOrderId)) {
                // פקודת כניסה
                if (orderId == state.parentOrderId && (!state.position || state.position === null)) {
                    log(`[SYNC] Entry order filled. Updating state to 'long'.`);
                    state.position = 'long';
                    state.entryPrice = avgFillPrice;
                    state.size = filled;
                    await setState('trade_state', state);
                } else if (orderId != state.parentOrderId && state.position === 'long') {
                // פקודת TP או SL התממשה (פקודת מכירה)
                    log(`[SYNC] Exit order (TP/SL) filled. Clearing trade-specific fields from state.`);
                    // טען את המצב הקיים, נקה רק את פרטי הפוזיציה, ושמור את השאר
                    let currentState = await getState('trade_state') || {};
                    delete currentState.position;
                    delete currentState.entryPrice;
                    delete currentState.size;
                    delete currentState.parentOrderId; // חשוב לנקות את מזהה הפקודה
                    await setState('trade_state', currentState);
                }
            }
        }
    } catch (e) {
        log(`[SYNC ERROR] Failed to update state on orderStatus: ${e.message}`, 'error');
    }
});
ib.on(EventName.error, (err, code, reqId) => {
    log(`[TWS ERROR] Code=${code}, ReqId=${reqId || 'N/A'}: ${err && err.message ? err.message : err}`,'error');
});

// --- פונקציות עזר ---
const getRealPositions = () => {
    return new Promise((resolve, reject) => {
        const positions = [];
        const onPosition = (account, contract, position, avgCost) => {
            if (position !== 0) {
                positions.push({ account, contract, position, avgCost });
            }
        };
        const onPositionEnd = () => {
            ib.off(EventName.position, onPosition);
            ib.off(EventName.positionEnd, onPositionEnd);
            resolve(positions);
        };
        
        const timeout = setTimeout(() => {
            ib.off(EventName.position, onPosition);
            ib.off(EventName.positionEnd, onPositionEnd);
            reject(new Error("Timeout waiting for position data."));
        }, 5000); // 5 שניות המתנה

        ib.on(EventName.position, onPosition);
        ib.on(EventName.positionEnd, onPositionEnd);
        ib.reqPositions();
    });
};

// === הגדרות מצב בדיקה נטענות מהקונפיג ===
const TEST_MODE_ENABLED = CONFIG.agent.TEST_MODE_ENABLED;
const TEST_BUY_QUANTITY = CONFIG.agent.TEST_BUY_QUANTITY;
const TEST_BUY_PRICE_FACTOR = CONFIG.agent.TEST_BUY_PRICE_FACTOR;
// ========================================

// --- לוגיקת מסחר ראשית ---
// עוזר: בדוק אם עכשיו זה market open (15:30 UTC עבור NYSE)
function isMarketOpenNow() {
    const now = new Date();
    return now.getUTCHours() === 15 && now.getUTCMinutes() === 30;
}


// --- Refactored modular trade cycle ---
async function handleManualCommands() {
    const commandPath = path.join(__dirname, 'command.json');
    let manualCommand = null;
    if (fs.existsSync(commandPath)) {
        try {
            const cmdRaw = fs.readFileSync(commandPath, 'utf-8');
            if (cmdRaw.trim()) {
                manualCommand = JSON.parse(cmdRaw);
            }
        } catch (e) {
            log(`Failed to read/parse command.json: ${e.message}`, 'error');
        }
    }
    if (manualCommand && manualCommand.command) {
        log(`[MANUAL COMMAND] Received: ${manualCommand.command}`);
        if (manualCommand.command.toUpperCase() === 'CLOSE_ALL') {
            try {
                const allPositions = await getRealPositions();
                for (const pos of allPositions) {
                    if (pos.position > 0) {
                        const contract = pos.contract;
                        const ibContract = new Stock(contract.symbol, contract.exchange, contract.currency);
                        ibContract.secType = contract.secType;
                        ibContract.primaryExch = contract.primaryExch;
                        const orderId = await new Promise((resolve) => {
                            ib.once(EventName.nextValidId, (id) => resolve(id));
                            ib.reqIds();
                        });
                        ib.placeOrder(orderId, ibContract, { action: 'SELL', orderType: 'MKT', totalQuantity: pos.position });
                        log(`[MANUAL COMMAND] Sent CLOSE ALL for ${contract.symbol}, qty ${pos.position}`);
                    }
                }
            } catch (e) {
                log(`[MANUAL COMMAND] Failed to close all positions: ${e.message}`, 'error');
            }
        } else if (manualCommand.command.toUpperCase() === 'PAUSE_NEW_ENTRIES') {
            try {
                let state = await getState('trade_state') || {};
                state.pause_new_entries = manualCommand.pause_new_entries === true;
                await setState('trade_state', state);
                log(`[MANUAL COMMAND] pause_new_entries set to ${state.pause_new_entries}`);
            } catch (e) {
                log(`[MANUAL COMMAND] Failed to set pause_new_entries: ${e.message}`, 'error');
            }
        } else if (manualCommand.command.toUpperCase() === 'RESTART_LOGIC') {
            try {
                await setState('trade_state', { position: null });
                log(`[MANUAL COMMAND] Logic state reset (trade_state cleared)`);
            } catch (e) {
                log(`[MANUAL COMMAND] Failed to reset logic: ${e.message}`, 'error');
            }
        } else {
            log(`[MANUAL COMMAND] Unknown command: ${manualCommand.command}`, 'warn');
        }
        try { fs.writeFileSync(commandPath, ''); } catch (e) { log(`Failed to clear command.json: ${e.message}`, 'error'); }
    }
}

async function syncWithPortfolio(ibContract) {
    log("Syncing with real portfolio...");
    const allPositions = await getRealPositions();
    const realPosition = allPositions.find(p => p.contract.symbol === ibContract.symbol);
    let state = await getState('trade_state') || { position: null };
    if (realPosition) {
        log(`Found REAL position in portfolio: ${realPosition.position} shares of ${realPosition.contract.symbol} at avg cost ${realPosition.avgCost}.`);
        if (state.position !== 'long' || state.size !== realPosition.position) {
            log('Local state is out of sync. Correcting it now.', 'warn');
            state = {
                position: 'long',
                size: realPosition.position,
                entryPrice: realPosition.avgCost
            };
            await setState('trade_state', state);
        }
    } else {
        log(`No real position for ${ibContract.symbol} found in portfolio.`);
        if (state.position === 'long') {
            log('Local state shows a position, but none exists in portfolio. Clearing local state.', 'warn');
            state = { position: null };
            await setState('trade_state', state);
        }
    }
    log(`Reconciled state is: Position=${state.position || 'None'}`);
    return state;
}

async function getPrediction() {
    // Use contract from CONFIG for historical data
    const contract = CONFIG.contract;
    if (!contract) {
        log("No contract found in CONFIG. Aborting prediction.", 'error');
        return null;
    }
    // Now get historical data for this contract
    log("Requesting historical data...");
    const ibContract = new Stock(contract.symbol, contract.exchange, contract.currency);
    ibContract.secType = contract.secType;
    ibContract.primaryExch = contract.primaryExch;
    const historicalData = await new Promise((resolve, reject) => {
        const data = [];
        const onHistoricalData = (reqId, date, open, high, low, close, volume) => {
            if (date.startsWith("finished")) resolve(data);
            else data.push({ date, open, high, low, close, volume });
        };
        ib.on(EventName.historicalData, onHistoricalData);
        ib.reqHistoricalData(1, ibContract, '', CONFIG.ib.history_window || '90 D', '1 day', 'TRADES', 1, 1);
        setTimeout(() => { ib.off(EventName.historicalData, onHistoricalData); reject(new Error("Timeout waiting for historical data")); }, 10000);
    });
    if (historicalData.length < 50) {
        log(`Not enough historical data: received ${historicalData.length} bars. Aborting.`, 'warn');
        return null;
    }
    log(`Received ${historicalData.length} bars of historical data.`);
    log("Sending data to model API...");
    let predictionResult;
    let lastError;
    for (let attempt = 1; attempt <= 3; attempt++) {
        try {
            const response = await axios.post(`${CONFIG.modelApiUrl}/predict`, { historical: historicalData });
            predictionResult = response.data;
            break;
        } catch (err) {
            lastError = err;
            log(`API request failed (attempt ${attempt}/3): ${err.message || err}`, 'warn');
            if (attempt < 3) {
                await new Promise(res => setTimeout(res, 1000));
            }
        }
    }
    if (!predictionResult) {
        log('Failed to get prediction from model API after 3 attempts.', 'error');
        throw lastError;
    }
    const { prediction, risk_params, contract: contractResp } = predictionResult;
    log(`API Response -> Prediction: ${prediction}`);
    const currentPrice = historicalData[historicalData.length - 1].close;
    return { prediction, currentPrice, historicalData, risk_params, contract: contractResp };
}

async function executeTestLogic(state, predictionObj, ibContract) {
    const { prediction, currentPrice } = predictionObj;
    log(`!!! TEST MODE IS ACTIVE !!!`, 'warn');
    if (!state.position && !state.intent) {
        if (prediction === 'Buy' && !isMarketOpenNow()) {
            log(`TEST MODE: Prediction is 'Buy'. Saving intent to buy at next market open.`);
            state.intent = 'buy';
            await setState('trade_state', state);
        } else if (state.intent === 'buy' && isMarketOpenNow()) {
            const testLimitPrice = (currentPrice * TEST_BUY_PRICE_FACTOR).toFixed(2);
            log(`TEST MODE: Executing pending BUY intent. Placing BUY LIMIT ${TEST_BUY_QUANTITY} shares @ ${testLimitPrice} for test.`);
            const orderId = await new Promise((resolve) => {
                ib.once(EventName.nextValidId, (id) => resolve(id));
                ib.reqIds();
            });
            log(`[DEBUG] Sending order details: ${JSON.stringify({ orderId, contract: ibContract, order: { action: 'BUY', orderType: 'LMT', totalQuantity: TEST_BUY_QUANTITY, lmtPrice: parseFloat(testLimitPrice) } }, null, 2)}`);
            ib.placeOrder(orderId, ibContract, { action: 'BUY', orderType: 'LMT', totalQuantity: TEST_BUY_QUANTITY, lmtPrice: parseFloat(testLimitPrice) });
            log(`TEST MODE: Order sent! Order ID: ${orderId}`, 'info');
            state = { position: 'long', entryPrice: currentPrice, size: TEST_BUY_QUANTITY, parentOrderId: orderId };
            await setState('trade_state', state);
        } else {
            log(`TEST MODE: No action taken. Prediction: ${prediction}, Intent: ${state.intent || 'None'}, Position: ${state.position || 'None'}`);
        }
    } else {
        log(`TEST MODE: No action taken. Prediction: ${prediction}, Intent: ${state.intent || 'None'}, Position: ${state.position || 'None'}`);
    }
}

async function executeProductionLogic(state, predictionObj, ibContract) {
    const { prediction, currentPrice, risk_params } = predictionObj;
    let accountBalance = null;
    try {
        accountBalance = await new Promise((resolve, reject) => {
            let resolved = false;
            const onUpdateAccountValue = (key, val, currency, accountName) => {
                if ((key === 'TotalCashValue' || key === 'NetLiquidation') && currency === 'USD') {
                    resolved = true;
                    ib.off(EventName.updateAccountValue, onUpdateAccountValue);
                    resolve(parseFloat(val));
                }
            };
            ib.on(EventName.updateAccountValue, onUpdateAccountValue);
            ib.reqAccountSummary(1, 'All', 'TotalCashValue,NetLiquidation');
            setTimeout(() => {
                ib.off(EventName.updateAccountValue, onUpdateAccountValue);
                if (!resolved) reject(new Error('Timeout fetching account balance from broker.'));
            }, 5000);
        });
        log(`Fetched account balance from broker: $${accountBalance}`);
    } catch (e) {
        log(`Failed to fetch account balance from broker: ${e.message}`, 'error');
        return;
    }
    if (prediction === 'Buy' && !state.position && !state.pause_new_entries) {
        const sl_pct = risk_params.stop_loss_pct / 100.0;
        const tp_pct = risk_params.take_profit_pct / 100.0;
        const rpt = risk_params.risk_per_trade;

        if (!sl_pct || sl_pct <= 0) {
            log('Invalid stop_loss_pct. Cannot place trade.', 'error'); return;
        }

        // חישוב גודל פוזיציה חדש
        const posSize = Math.max(1, Math.floor((accountBalance * rpt) / (currentPrice * sl_pct)));
        // חישוב מחירי SL/TP חדשים
        const slPrice = (currentPrice * (1 - sl_pct)).toFixed(2);
        const tpPrice = (currentPrice * (1 + tp_pct)).toFixed(2);

        log(`Placing Bracket Order: BUY ${posSize} @ MKT, TP @ ${tpPrice}, SL @ ${slPrice}`);
        const orders = await ib.placeBracketOrder(ibContract,
            { action: 'BUY', orderType: 'MKT', totalQuantity: posSize },
            { action: 'SELL', orderType: 'LMT', totalQuantity: posSize, lmtPrice: tpPrice },
            { action: 'SELL', orderType: 'STP', totalQuantity: posSize, auxPrice: slPrice }
        );
        await setState('trade_state', { position: 'long', size: posSize, parentOrderId: orders[0]?.orderId });
    } else if (prediction === 'Buy' && !state.position && state.pause_new_entries) {
        log("Skipping new trade entry because 'pause_new_entries' flag is active.");
    // removed closing on 'Hold' signal; only bracket order exits are allowed
    } else {
        log(`No action taken. Prediction: ${prediction}, Position: ${state.position || 'None'}`);
    }
}

// Dispatcher function
async function executeTradingLogic(state, predictionResult, ibContract) {
    if (TEST_MODE_ENABLED) {
        await executeTestLogic(state, predictionResult, ibContract);
    } else {
        await executeProductionLogic(state, predictionResult, ibContract);
    }
}

async function executeTradeCycle() {
    log("--- Starting Trade Cycle ---");
    try {
        await handleManualCommands();
        // Get prediction, risk_params, and contract in one API call
        const predictionResult = await getPrediction();
        if (!predictionResult) return;
        const { contract } = predictionResult;
        const ibContract = new Stock(contract.symbol, contract.exchange, contract.currency);
        ibContract.secType = contract.secType;
        ibContract.primaryExch = contract.primaryExch;
        const state = await syncWithPortfolio(ibContract);
        await executeTradingLogic(state, predictionResult, ibContract);
    } catch (err) {
        log(`Error in trade cycle: ${err.message}`, 'error');
    } finally {
        log("--- Trade Cycle Ended ---");
    }
}


// --- פונקציית הפעלה ראשית ---
async function startAgent() {
    try {
        log("Agent starting...");
        ib.connect();
        
        ib.on(EventName.connected, async () => {
            log("IB API Connected.");
            await executeTradeCycle(); // הרצה ראשונה מיידית
            
            cron.schedule('30 21 * * 1-5', executeTradeCycle, { timezone: "UTC" });
            log("Cron job scheduled for 21:30 UTC, Mon-Fri.");
        });

        ib.on(EventName.error, (err, code, reqId) => {
            log(`[TWS ERROR] Code=${code}, ReqId=${reqId || 'N/A'}: ${err && err.message ? err.message : err}`,'error');
        });

    } catch (err) {
        log(`FATAL STARTUP ERROR: ${err.message}`, 'error');
        process.exit(1);
    }
}

startAgent();
