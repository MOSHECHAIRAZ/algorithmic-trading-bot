"""
קובץ זה מכיל את כל הנתיבים הקשורים לניהול תהליכים במערכת
"""

from flask import Blueprint, jsonify, request
import logging
import os
import sys
import subprocess
import threading
import time
from datetime import datetime

# יצירת Blueprint עבור ניהול תהליכים
processes_bp = Blueprint('processes', __name__, url_prefix='/api/processes')

# מילון לשמירת תהליכים פעילים
active_processes = {}
process_lock = threading.Lock()

def get_process_info(process_id):
    """מחזיר מידע על תהליך לפי המזהה שלו"""
    with process_lock:
        if process_id not in active_processes:
            return None
            
        proc = active_processes[process_id]
        return {
            "id": process_id,
            "name": proc.get("name", "Unknown"),
            "command": proc.get("command", ""),
            "start_time": proc.get("start_time", ""),
            "status": "running" if proc.get("process") and proc["process"].poll() is None else "stopped",
            "exit_code": proc["process"].poll() if proc.get("process") else None
        }

@processes_bp.route('/list', methods=['GET'])
def list_processes():
    """מחזיר רשימה של כל התהליכים הפעילים"""
    processes_info = []
    with process_lock:
        for pid, proc in active_processes.items():
            if proc.get("process"):
                status = "running" if proc["process"].poll() is None else "stopped"
                exit_code = proc["process"].poll()
                
                processes_info.append({
                    "id": pid,
                    "name": proc.get("name", "Unknown"),
                    "command": proc.get("command", ""),
                    "start_time": proc.get("start_time", ""),
                    "status": status,
                    "exit_code": exit_code
                })
    
    return jsonify(processes_info)

@processes_bp.route('/start', methods=['POST'])
def start_process():
    """מתחיל תהליך חדש"""
    try:
        data = request.json
        process_name = data.get('name', 'Unknown Process')
        command = data.get('command')
        
        if not command:
            return jsonify({"status": "error", "message": "No command specified"}), 400
            
        # פתיחת התהליך
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # יצירת מזהה תהליך ייחודי
        process_id = f"{process_name}_{int(time.time())}"
        
        # שמירת מידע על התהליך
        with process_lock:
            active_processes[process_id] = {
                "name": process_name,
                "command": command,
                "process": process,
                "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return jsonify({
            "status": "success", 
            "message": f"Process {process_name} started", 
            "process_id": process_id
        })
        
    except Exception as e:
        logging.error(f"Error starting process: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@processes_bp.route('/stop/<process_id>', methods=['POST'])
def stop_process(process_id):
    """עוצר תהליך פעיל לפי המזהה שלו"""
    with process_lock:
        if process_id not in active_processes:
            return jsonify({"status": "error", "message": f"Process {process_id} not found"}), 404
            
        proc_info = active_processes[process_id]
        process = proc_info.get("process")
        
        if process and process.poll() is None:
            try:
                process.terminate()
                # המתנה קצרה לסיום התהליך
                for _ in range(5):
                    if process.poll() is not None:
                        break
                    time.sleep(0.1)
                    
                # אם התהליך עדיין רץ, הורג אותו בכוח
                if process.poll() is None:
                    process.kill()
                    
                return jsonify({
                    "status": "success", 
                    "message": f"Process {proc_info.get('name', process_id)} stopped"
                })
            except Exception as e:
                logging.error(f"Error stopping process {process_id}: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        else:
            return jsonify({
                "status": "warning", 
                "message": f"Process {proc_info.get('name', process_id)} already stopped"
            })

@processes_bp.route('/output/<process_id>', methods=['GET'])
def get_process_output(process_id):
    """מחזיר את הפלט של תהליך פעיל"""
    with process_lock:
        if process_id not in active_processes:
            return jsonify({"status": "error", "message": f"Process {process_id} not found"}), 404
            
        proc_info = active_processes[process_id]
        process = proc_info.get("process")
        
        if not process:
            return jsonify({"status": "error", "message": "Process information incomplete"}), 500
            
        # קריאת הפלט והשגיאות מהתהליך
        try:
            # אם התהליך פעיל, מקבלים את הפלט הקיים בלי לחכות לסיום
            if process.poll() is None:
                # שימוש בקבוע כדי לקרוא פלט מידי (ללא חסימה)
                import select
                readable_stdout = select.select([process.stdout], [], [], 0)[0]
                readable_stderr = select.select([process.stderr], [], [], 0)[0]
                
                stdout = ""
                stderr = ""
                
                if readable_stdout:
                    stdout = process.stdout.read()
                if readable_stderr:
                    stderr = process.stderr.read()
            else:
                # התהליך הסתיים, אפשר לקרוא את כל הפלט
                stdout, stderr = process.communicate(timeout=1)
                
            return jsonify({
                "status": "success",
                "process_status": "running" if process.poll() is None else "stopped",
                "exit_code": process.poll(),
                "stdout": stdout or "",
                "stderr": stderr or ""
            })
            
        except Exception as e:
            logging.error(f"Error getting process output for {process_id}: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

# נתיבים ספציפיים להפעלת תהליכים מוגדרים מראש

@processes_bp.route('/run/ibkr', methods=['POST'])
def start_ibkr_gateway():
    """מפעיל את ה-IBKR Gateway"""
    try:
        # הפעלת תהליך ה-Gateway
        command = f"{sys.executable} start_ibkr.py"
        
        # יצירת תהליך דרך API התהליכים הכללי
        response = start_process()
        data = response.json
        
        if response.status_code == 200 and data.get("status") == "success":
            return jsonify({"status": "success", "message": "IBKR Gateway startup process initiated"})
        else:
            return jsonify({"status": "error", "message": data.get("message", "Unknown error")}), response.status_code
            
    except Exception as e:
        logging.error(f"Error starting IBKR Gateway: {e}")
        return jsonify({"status": "error", "message": f"Failed to start IBKR Gateway: {str(e)}"}), 500
