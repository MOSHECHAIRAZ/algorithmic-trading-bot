"""
process_manager.py - מודול לניהול תהליכים במערכת

מודול זה מרכז את כל הפונקציונליות הקשורה להפעלה, עצירה וניטור של תהליכים במערכת.
"""

import os
import sys
import subprocess
import threading
import time
import logging
import signal
from datetime import datetime
from typing import Dict, Optional, List, Tuple, Any, Union

logger = logging.getLogger(__name__)

class ProcessManager:
    """
    מנהל תהליכים לשליטה בתהליכי משנה של המערכת
    """
    
    def __init__(self):
        """
        אתחול מנהל התהליכים
        """
        self.processes: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
    def start_process(self, 
                     process_id: str, 
                     command: str, 
                     name: str = None, 
                     cwd: str = None, 
                     env: Dict[str, str] = None, 
                     shell: bool = True) -> Dict[str, Any]:
        """
        מפעיל תהליך חדש
        
        Args:
            process_id: מזהה ייחודי לתהליך
            command: הפקודה להפעלה
            name: שם ידידותי לתהליך
            cwd: תיקיית עבודה
            env: משתני סביבה
            shell: האם להפעיל עם shell
            
        Returns:
            מילון עם סטטוס הפעלת התהליך
        """
        with self.lock:
            if process_id in self.processes and self.is_process_running(process_id):
                return {
                    "status": "warning", 
                    "message": f"Process {process_id} is already running",
                    "process_id": process_id
                }
                
            try:
                logger.info(f"Starting process: {command}")
                
                # יצירת תהליך חדש
                process = subprocess.Popen(
                    command,
                    shell=shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    cwd=cwd,
                    env=env
                )
                
                # שמירת מידע על התהליך
                self.processes[process_id] = {
                    "process": process,
                    "command": command,
                    "name": name or process_id,
                    "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "output": [],
                    "error": []
                }
                
                # הפעלת thread לקריאת הפלט של התהליך
                self._start_output_reader(process_id)
                
                return {
                    "status": "success", 
                    "message": f"Process {process_id} started successfully",
                    "process_id": process_id
                }
                
            except Exception as e:
                error_msg = f"Error starting process {process_id}: {str(e)}"
                logger.error(error_msg)
                return {
                    "status": "error", 
                    "message": error_msg,
                    "process_id": process_id
                }
    
    def stop_process(self, process_id: str, force: bool = False, timeout: int = 5) -> Dict[str, Any]:
        """
        עוצר תהליך לפי המזהה שלו
        
        Args:
            process_id: מזהה התהליך
            force: האם להשתמש בכוח (SIGKILL במקום SIGTERM)
            timeout: זמן המתנה בשניות לפני שימוש בכוח
            
        Returns:
            מילון עם סטטוס העצירה
        """
        with self.lock:
            if process_id not in self.processes:
                return {
                    "status": "error", 
                    "message": f"Process {process_id} not found",
                    "process_id": process_id
                }
                
            proc_info = self.processes[process_id]
            process = proc_info["process"]
            
            if process.poll() is not None:
                return {
                    "status": "warning", 
                    "message": f"Process {process_id} already stopped",
                    "process_id": process_id,
                    "exit_code": process.returncode
                }
                
            try:
                logger.info(f"Stopping process: {process_id}")
                
                if force:
                    # עצירה בכוח
                    process.kill()
                else:
                    # עצירה רגילה
                    process.terminate()
                    
                    # המתנה לסיום
                    for _ in range(timeout * 10):
                        if process.poll() is not None:
                            break
                        time.sleep(0.1)
                        
                    # אם התהליך עדיין רץ, משתמש בכוח
                    if process.poll() is None:
                        logger.warning(f"Process {process_id} did not terminate gracefully, killing it")
                        process.kill()
                
                # המתנה קצרה לסיום התהליך
                process.wait(timeout=1)
                
                return {
                    "status": "success", 
                    "message": f"Process {process_id} stopped",
                    "process_id": process_id,
                    "exit_code": process.returncode
                }
                
            except Exception as e:
                error_msg = f"Error stopping process {process_id}: {str(e)}"
                logger.error(error_msg)
                return {
                    "status": "error", 
                    "message": error_msg,
                    "process_id": process_id
                }
    
    def is_process_running(self, process_id: str) -> bool:
        """
        בודק אם תהליך רץ לפי המזהה שלו
        
        Args:
            process_id: מזהה התהליך
            
        Returns:
            האם התהליך רץ
        """
        with self.lock:
            if process_id not in self.processes:
                return False
                
            process = self.processes[process_id]["process"]
            return process.poll() is None
    
    def get_process_info(self, process_id: str) -> Optional[Dict[str, Any]]:
        """
        מחזיר מידע על תהליך לפי המזהה שלו
        
        Args:
            process_id: מזהה התהליך
            
        Returns:
            מילון עם מידע על התהליך, או None אם לא נמצא
        """
        with self.lock:
            if process_id not in self.processes:
                return None
                
            proc_info = self.processes[process_id]
            process = proc_info["process"]
            
            return {
                "id": process_id,
                "name": proc_info.get("name", "Unknown"),
                "command": proc_info.get("command", ""),
                "start_time": proc_info.get("start_time", ""),
                "status": "running" if process.poll() is None else "stopped",
                "exit_code": process.poll(),
                "output_size": len(proc_info.get("output", [])),
                "error_size": len(proc_info.get("error", []))
            }
    
    def get_all_processes(self) -> List[Dict[str, Any]]:
        """
        מחזיר מידע על כל התהליכים
        
        Returns:
            רשימה של מילונים עם מידע על התהליכים
        """
        process_list = []
        
        with self.lock:
            for pid in self.processes:
                info = self.get_process_info(pid)
                if info:
                    process_list.append(info)
                    
        return process_list
    
    def get_process_output(self, process_id: str, max_lines: int = 100) -> Dict[str, Any]:
        """
        מחזיר את הפלט של תהליך
        
        Args:
            process_id: מזהה התהליך
            max_lines: מספר השורות המקסימלי להחזרה
            
        Returns:
            מילון עם הפלט הסטנדרטי והשגיאות
        """
        with self.lock:
            if process_id not in self.processes:
                return {
                    "status": "error", 
                    "message": f"Process {process_id} not found",
                    "stdout": "",
                    "stderr": ""
                }
                
            proc_info = self.processes[process_id]
            process = proc_info["process"]
            
            # קבלת הפלט הנוכחי
            stdout_lines = proc_info.get("output", [])
            stderr_lines = proc_info.get("error", [])
            
            # הגבלת מספר השורות
            if max_lines > 0:
                stdout_lines = stdout_lines[-max_lines:]
                stderr_lines = stderr_lines[-max_lines:]
                
            return {
                "status": "success",
                "process_status": "running" if process.poll() is None else "stopped",
                "exit_code": process.poll(),
                "stdout": "\n".join(stdout_lines),
                "stderr": "\n".join(stderr_lines)
            }
    
    def clean_stopped_processes(self) -> int:
        """
        מנקה תהליכים שהסתיימו מהזיכרון
        
        Returns:
            מספר התהליכים שנוקו
        """
        cleaned_count = 0
        
        with self.lock:
            pids_to_remove = []
            
            for pid, proc_info in self.processes.items():
                process = proc_info["process"]
                
                if process.poll() is not None:
                    pids_to_remove.append(pid)
            
            for pid in pids_to_remove:
                del self.processes[pid]
                cleaned_count += 1
                
        return cleaned_count
    
    def _start_output_reader(self, process_id: str) -> None:
        """
        מפעיל thread שקורא את הפלט של התהליך
        
        Args:
            process_id: מזהה התהליך
        """
        if process_id not in self.processes:
            return
            
        proc_info = self.processes[process_id]
        process = proc_info["process"]
        
        def read_output():
            while process.poll() is None:
                # קריאת שורה מהפלט הסטנדרטי
                stdout_line = process.stdout.readline().strip()
                if stdout_line:
                    with self.lock:
                        if "output" not in proc_info:
                            proc_info["output"] = []
                        proc_info["output"].append(stdout_line)
                        
                # קריאת שורה מהשגיאות
                stderr_line = process.stderr.readline().strip()
                if stderr_line:
                    with self.lock:
                        if "error" not in proc_info:
                            proc_info["error"] = []
                        proc_info["error"].append(stderr_line)
                        
                # המתנה קצרה כדי לא להעמיס על המעבד
                if not stdout_line and not stderr_line:
                    time.sleep(0.1)
                    
            # קריאת שאר הפלט אחרי סיום התהליך
            remaining_stdout, remaining_stderr = process.communicate()
            
            if remaining_stdout:
                with self.lock:
                    if "output" not in proc_info:
                        proc_info["output"] = []
                    proc_info["output"].extend(remaining_stdout.splitlines())
                    
            if remaining_stderr:
                with self.lock:
                    if "error" not in proc_info:
                        proc_info["error"] = []
                    proc_info["error"].extend(remaining_stderr.splitlines())
        
        # הפעלת ה-thread
        thread = threading.Thread(target=read_output)
        thread.daemon = True
        thread.start()

# יצירת מופע גלובלי של מנהל התהליכים
process_manager = ProcessManager()
