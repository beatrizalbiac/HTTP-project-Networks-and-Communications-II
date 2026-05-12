import customtkinter as ctk
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from client import HTTPClient

API_KEY = os.environ.get("API_KEY", "")

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("themes/lavender.json")


class GUIClient:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Bunnies HTTP Client")
        self.root.geometry("900x400")
        self._build_ui()

    def _build_ui(self):
        # Top bar
        top = ctk.CTkFrame(self.root, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(12, 4))

        self.method_var = ctk.StringVar(value="GET")
        ctk.CTkOptionMenu(top, variable=self.method_var, width=90,
                          values=["GET", "POST", "PUT", "DELETE", "HEAD"]
                          ).pack(side="left", padx=(0, 6))

        self.url_var = ctk.StringVar(value="http://localhost:8080/bunnies")
        ctk.CTkEntry(top, textvariable=self.url_var, font=("Courier", 18)
                     ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(top, text="Send", width=80, command=self._send
                      ).pack(side="left")

        # API key
        key_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        key_frame.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(key_frame, text="API Key:").pack(side="left")
        self.key_var = ctk.StringVar(value="")
        ctk.CTkEntry(key_frame, textvariable=self.key_var, width=220
                     ).pack(side="left", padx=6)

        # Body + Response
        panels = ctk.CTkFrame(self.root, fg_color="transparent")
        panels.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        panels.columnconfigure(0, weight=2)
        panels.columnconfigure(1, weight=1)
        panels.rowconfigure(1, weight=1)

        ctk.CTkLabel(panels, text="Request body").grid(row=0, column=0, sticky="w", pady=(0, 2))
        ctk.CTkLabel(panels, text="Response").grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 2))

        self.body_text = ctk.CTkTextbox(panels, font=("Courier", 15), wrap="none")
        self.body_text.grid(row=1, column=0, sticky="nsew")

        resp_frame = ctk.CTkFrame(panels, fg_color="transparent")
        resp_frame.grid(row=1, column=1, sticky="nsew", padx=(12, 0))
        resp_frame.rowconfigure(1, weight=1)
        resp_frame.columnconfigure(0, weight=1)

        self.status_var = ctk.StringVar(value="—")
        ctk.CTkLabel(resp_frame, textvariable=self.status_var,
                     font=("Courier", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.resp_text = ctk.CTkTextbox(resp_frame, font=("Courier", 15), wrap="none", state="disabled")
        self.resp_text.grid(row=1, column=0, sticky="nsew")

    def _send(self):
        method = self.method_var.get()
        url = self.url_var.get().strip()
        api_key = self.key_var.get().strip() or None
        body_str = self.body_text.get("1.0", "end").strip()

        body = body_str.encode("utf-8") if body_str else None
        headers = {"Content-Type": "application/json"} if body else {}

        self._set_response("Sending...", "")

        try:
            with HTTPClient(api_key=api_key) as c:
                resp = c.request(method, url, headers=headers or None, body=body)

            ct = resp.headers.get("content-type", "")
            if "application/json" in ct:
                try:
                    body_display = json.dumps(resp.json(), indent=2, ensure_ascii=False)
                except Exception:
                    body_display = resp.text()
            else:
                body_display = resp.text()

            header_lines = "\n".join(f"{k}: {v}" for k, v in resp.headers.items())
            self._set_response(
                f"HTTP/1.1 {resp.status_code} {resp.status_text}",
                header_lines + "\n\n" + body_display
            )

        except Exception as e:
            self._set_response("ERROR", str(e))

    def _set_response(self, status: str, body: str):
        self.status_var.set(status)
        self.resp_text.configure(state="normal")
        self.resp_text.delete("1.0", "end")
        self.resp_text.insert("end", body)
        self.resp_text.configure(state="disabled")


def main():
    root = ctk.CTk()
    GUIClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()