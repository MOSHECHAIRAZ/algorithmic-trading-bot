"""
routes/agent.py - נתיבי סוכן המסחר

נתיבים הקשורים לסוכן המסחר ופעולותיו
"""

from flask import Blueprint, jsonify, request
import logging
import os
import json
import datetime

agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')

@agent_bp.route('/position', methods=['GET'])
def get_position():
    """מחזיר מידע על הפוזיציה הנוכחית של סוכן המסחר"""
    try:
        # קובץ לדוגמה שבו נשמר מצב הפוזיציה
        position_file = os.path.join('agent', 'state.json')
        
        # אם הקובץ קיים, נקרא את המידע
        if os.path.exists(position_file):
            try:
                with open(position_file, 'r') as f:
                    state = json.load(f)
                
                # נבדוק אם יש פוזיציה פעילה
                if state.get('position') and state['position'] != 'none':
                    return jsonify({
                        'position': state.get('position', 'none'),
                        'symbol': state.get('symbol', 'SPY'),
                        'size': state.get('size', 0),
                        'entryPrice': state.get('entry_price'),
                        'stopLoss': state.get('stop_loss'),
                        'takeProfit': state.get('take_profit'),
                        'entryTime': state.get('entry_time')
                    })
            except Exception as e:
                logging.error(f"Error reading position state: {e}")
        
        # אם אין פוזיציה פעילה או הקובץ לא קיים
        return jsonify({'position': 'none'})
    except Exception as e:
        logging.error(f"Error getting position: {e}")
        return jsonify({'position': 'none', 'error': str(e)})

@agent_bp.route('/command/history', methods=['GET'])
def get_command_history():
    """מחזיר היסטוריית פקודות של סוכן המסחר"""
    try:
        # קובץ לדוגמה שבו נשמרת היסטוריית הפקודות
        command_file = os.path.join('agent', 'command.json')
        
        if os.path.exists(command_file):
            try:
                with open(command_file, 'r') as f:
                    commands = json.load(f)
                return jsonify({"commands": commands.get('commands', [])})
            except Exception as e:
                logging.error(f"Error reading command history: {e}")
        
        # אם הקובץ לא קיים, נחזיר רשימה ריקה
        return jsonify({"commands": []})
    except Exception as e:
        logging.error(f"Error getting command history: {e}")
        return jsonify({"commands": [], "error": str(e)})

@agent_bp.route('/command', methods=['POST'])
def send_command():
    """שולח פקודה לסוכן המסחר"""
    try:
        command_data = request.json
        if not command_data or 'command' not in command_data:
            return jsonify({"status": "error", "message": "No command specified"}), 400
        
        # קובץ לדוגמה שבו נשמרות הפקודות
        command_file = os.path.join('agent', 'command.json')
        
        # יצירת רשומת פקודה חדשה
        new_command = {
            "command": command_data['command'],
            "timestamp": datetime.datetime.now().isoformat(),
            "params": command_data.get('params', {})
        }
        
        # עדכון הקובץ
        if os.path.exists(command_file):
            try:
                with open(command_file, 'r') as f:
                    commands = json.load(f)
            except:
                commands = {"commands": []}
        else:
            commands = {"commands": []}
        
        commands["commands"].insert(0, new_command)
        
        # שמירה חזרה לקובץ
        os.makedirs(os.path.dirname(command_file), exist_ok=True)
        with open(command_file, 'w') as f:
            json.dump(commands, f, indent=2)
        
        return jsonify({"status": "success", "message": "Command sent"})
    except Exception as e:
        logging.error(f"Error sending command: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
