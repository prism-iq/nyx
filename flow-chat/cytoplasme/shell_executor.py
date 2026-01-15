import subprocess
import json
import sys
import os
import traceback
from typing import Dict, Any, Optional

class ShellExecutor:
    def __init__(self):
        self.last_output = ""
        self.last_error = ""
        
    def execute(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute shell command with proper error handling"""
        try:
            # Set environment variables
            env = os.environ.copy()
            env['GOCACHE'] = '/tmp/go-cache'
            env['GOPATH'] = '/opt/go'
            env['PATH'] = env.get('PATH', '') + ':/usr/local/go/bin'
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd='/opt/flow-chat'
            )
            
            self.last_output = result.stdout
            self.last_error = result.stderr
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "error": result.stderr.strip(),
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Command timed out after {timeout}s",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Execution error: {str(e)}",
                "returncode": -2
            }

# Global executor instance
executor = ShellExecutor()

def execute_command(command: str) -> Dict[str, Any]:
    """Main execution function"""
    return executor.execute(command)