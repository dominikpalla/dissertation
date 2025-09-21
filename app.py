import os
import sys
import importlib.util
import threading
import time
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
from interpreter import interpret_step, save_spec
from cogen import generate_module
from validation import validate_module
from feedback import process_report

BASE_DIR = Path(__file__).parent
MODULES_DIR = BASE_DIR / "modules"
DATA_DIR = BASE_DIR / "data"

progress_state = {"progress": 0, "message": ""}
chat_history = []  # udržujeme historii konverzace


def register_blueprints(app):
    """Import all generated modules and register their blueprints."""
    for mod_path in MODULES_DIR.iterdir():
        if mod_path.is_dir() and (mod_path / "__init__.py").exists():
            module_name = f"modules.{mod_path.name}"

            if module_name in sys.modules:
                del sys.modules[module_name]

            spec = importlib.util.spec_from_file_location(
                module_name, mod_path / "__init__.py"
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            if hasattr(module, "bp") and mod_path.name not in app.blueprints:
                app.register_blueprint(module.bp)
                print(f"✅ Registered blueprint: {mod_path.name}")


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")
    MODULES_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    register_blueprints(app)

    # --- Homepage (chat UI) ---
    @app.route("/", methods=["GET"])
    def index():
        existing = []
        if MODULES_DIR.exists():
            for p in MODULES_DIR.iterdir():
                if p.is_dir() and (p / "__init__.py").exists():
                    existing.append(p.name)

        html = """
        <html>
          <head>
            <meta charset="utf-8"/>
            <title>Mini GAI CRM Demo</title>
            <style>
              body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:900px;margin:40px auto;padding:0 16px;}
              .card{border:1px solid #ddd;border-radius:12px;padding:16px;margin:16px 0;box-shadow:0 2px 6px rgba(0,0,0,0.04);}
              #chatBox{max-height:400px;overflow-y:auto;border:1px solid #ddd;padding:10px;border-radius:6px;background:#fafafa;}
              .msg{margin:6px 0;}
              .bot{color:#111;}
              .user{color:#006;}
              .inputRow{display:flex;gap:8px;margin-top:10px;}
              input[type=text]{flex:1;padding:8px;border:1px solid #ccc;border-radius:6px;}
              button{padding:8px 14px;border:0;border-radius:8px;background:#111;color:#fff;cursor:pointer}
              button:hover{background:#333}
              .chips span{display:inline-block;background:#f2f2f2;border-radius:14px;padding:6px 10px;margin:4px 6px;font-size:14px}
              a{color:#0b5; text-decoration:none}
              a:hover{text-decoration:underline}
            </style>
          </head>
          <body>
            <h1>Mini GAI CRM Demo</h1>

            <div class="card">
              <h3>AI Chat Specification Assistant</h3>
              <div id="chatBox"></div>
              <div class="inputRow">
                <input id="userInput" type="text" placeholder="Type your answer..."/>
                <button id="sendBtn">Send</button>
              </div>
            </div>

            <div class="card">
              <h3>Existing modules</h3>
              {% if existing %}
                <div class="chips">
                  {% for m in existing %}
                    <span>{{ m }} — <a href="/{{ m }}/">open</a></span>
                  {% endfor %}
                </div>
              {% else %}
                <p>No modules yet.</p>
              {% endif %}
            </div>

            <p style="opacity:.6">Dominik Palla - Dissertation Demo</p>

            <script>
              const chatBox=document.getElementById("chatBox");
              const sendBtn=document.getElementById("sendBtn");
              const userInput=document.getElementById("userInput");

              function addMessage(sender,text){
                const div=document.createElement("div");
                div.className="msg "+sender;
                div.innerHTML = sender==="bot" ? "🤖: "+text : "👤: "+text;
                chatBox.appendChild(div);
                chatBox.scrollTop=chatBox.scrollHeight;
              }

              function sendMessage(){
                const val=userInput.value.trim();
                if(!val) return;
                addMessage("user",val);
                fetch("/chat_step",{
                  method:"POST",
                  headers:{"Content-Type":"application/json"},
                  body:JSON.stringify({msg:val})
                })
                .then(r=>r.json())
                .then(data=>{
                  if(data.message){ addMessage("bot",data.message); }
                  if(data.status==="final"){ setTimeout(()=>{window.location.reload();},1500); }
                });
                userInput.value="";
              }

              sendBtn.addEventListener("click", sendMessage);

              userInput.addEventListener("keypress",(e)=>{
                if(e.key==="Enter"){
                  e.preventDefault();
                  sendMessage();
                }
              });

              // Start conversation
              window.onload=()=>{
                addMessage("bot","Hi! Describe the entity you want to track (e.g., 'Computer with RAM, CPU, SSD').");
                userInput.focus();
              }
            </script>
          </body>
        </html>
        """
        return render_template_string(html, existing=existing)

    # --- Chat step ---
    @app.post("/chat_step")
    def chat_step():
        data = request.get_json(force=True)
        user_msg = data.get("msg", "")

        chat_history.append({"role": "user", "content": user_msg})
        spec, reply, done = interpret_step(chat_history)

        if done:
            if spec and spec.get("entities"):
                save_spec(spec, "latest")
                # 1) vygeneruj modul
                generate_module(spec)
                # 2) spusť validaci
                report = validate_module(spec)

                if report.get("status") == "ok":
                    progress_state["progress"] = 100
                    progress_state["message"] = "Restarting..."

                    def restart():
                        time.sleep(1.0)
                        os.execv(sys.executable, [sys.executable] + sys.argv)

                    threading.Thread(target=restart).start()
                    return jsonify({"status": "final", "message": "✅ Module generated & validated. Restarting…"})

                # 3) předat feedbacku
                fb = process_report(report, chat_history, spec)

                if fb.get("next_action") == "auto_fix":
                    generate_module(spec)
                    report2 = validate_module(spec)
                    if report2.get("status") == "ok":
                        def restart():
                            time.sleep(1.0)
                            os.execv(sys.executable, [sys.executable] + sys.argv)
                        threading.Thread(target=restart).start()
                        return jsonify({"status": "final", "message": "✅ Auto-fix successful. Restarting…"})
                    else:
                        msg = fb.get("message", "") + "\\n\\nAuto-fix did not resolve all issues. What should I do next?"
                        return jsonify({"status": "question", "message": msg})

                return jsonify({"status": "question", "message": fb.get("message", "Validation issues found.")})

            else:
                return jsonify({"status": "error", "message": "❌ No valid spec found, cannot generate module."})

        return jsonify({"status": "question", "message": reply})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)