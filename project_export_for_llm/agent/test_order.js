// test_order.js (גרסה עם אימות חוזה)
const { IBApi, EventName, Stock } = require('@stoqey/ib');

const IB_HOST = '127.0.0.1';
const IB_PORT = 4001;
const IB_CLIENT_ID = 200;

const ib = new IBApi({ host: IB_HOST, port: IB_PORT, clientId: IB_CLIENT_ID, show_raw_messages: false });

ib.on(EventName.error, (err, code, reqId) => {
    console.error(`[TWS ERROR] Code=${code}, ReqId=${reqId}: ${err && err.message ? err.message : err}`);
});

ib.on(EventName.openOrder, (orderId, contract, order, orderState) => {
    console.log(`[EVENT openOrder] OrderId: ${orderId}, Status: ${orderState.status}, Symbol: ${contract.symbol}`);
});

ib.on(EventName.orderStatus, (orderId, status, filled, remaining, avgFillPrice) => {
    console.log(`[EVENT orderStatus] OrderId: ${orderId}, Status: ${status}, Filled: ${filled}, Remaining: ${remaining}`);
    if (status === 'Submitted' || status === 'Filled' || status === 'Cancelled' || status === 'Inactive') {
        ib.disconnect();
        console.log("Disconnected.");
    }
});

// פונקציה לאימות חוזה (qualify contract) ב-@stoqey/ib
function qualifyContract(ib, contract) {
    return new Promise((resolve, reject) => {
        let resolved = false;
        ib.once(EventName.contractDetails, (reqId, details) => {
            resolved = true;
            resolve(details.contract);
        });
        ib.once(EventName.contractDetailsEnd, (reqId) => {
            if (!resolved) reject(new Error("No contract details found"));
        });
        ib.reqContractDetails(1, contract);
        setTimeout(() => {
            if (!resolved) reject(new Error("Timeout waiting for contract details"));
        }, 5000);
    });
}

async function runTest() {
    try {
        await ib.connect();
        console.log("Connected to IBKR.");

        // שלב 1: הגדרת חוזה בסיסי
        const contractToQualify = new Stock('SPY', 'SMART', 'USD');
        console.log("Qualifying contract...");
        const verifiedContract = await qualifyContract(ib, contractToQualify);
        console.log("Contract qualified successfully:", JSON.stringify(verifiedContract));

        // קבל Order ID תקין מה-API
        const orderId = await new Promise((resolve) => {
            ib.once(EventName.nextValidId, (id) => resolve(id));
            ib.reqIds();
        });
        console.log(`Next valid Order ID: ${orderId}`);

        const order = {
            action: 'BUY',
            orderType: 'LMT',
            totalQuantity: 1,
            lmtPrice: 500.00,
            transmit: true // הוספת transmit: true
        };

        // שלב 3: שלח את הפקודה עם החוזה המאומת והמדויק
        console.log('Placing order with verified contract...');
        ib.placeOrder(orderId, verifiedContract, order);
        console.log('placeOrder function was called. Waiting for events...');

    } catch (e) {
        console.error("Test script failed:", e.message);
        ib.disconnect();
    }
}

runTest();
