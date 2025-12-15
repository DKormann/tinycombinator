from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import random

from typing import Dict, Tuple, Union


@dataclass
class HTML:
  tag: str
  attrs: Dict[str, str]
  content: Tuple[Union[str, "HTML"]]
  def code(self):
    attrs = " ".join([f"{k}=\"{v}\"" for k, v in self.attrs.items()])
    content = "".join([item.code() if isinstance(item, HTML) else str(item) for item in self.content])
    return f'''<{self.tag} {attrs}>{content}</{self.tag}>'''

  @staticmethod
  def html(tag: str):
    def mk(*content: Union[str, "HTML"], **attrs: Dict[str, str]):
      return HTML(tag=tag, attrs=attrs, content=content)
    return mk

p = HTML.html("p")
h1 = HTML.html("h1")
h2 = HTML.html("h2")
h3 = HTML.html("h3")
div = HTML.html("div")
span = HTML.html("span")
script = HTML.html("script")
style = HTML.html("style")

button = HTML.html("button")
check = random.randint(0, 10_000)
out = []


def page(*content: HTML):
  return HTML.html("html")(
    HTML.html("head")(
      style(
        '''
        body {
          --background: #f0f0f0; --color: #000000;
          color: var(--color);
          background: var(--background);
          font-family: monospace;
        }

        @media (prefers-color-scheme: dark) {body {--background: #000000; --color: #f0f0f0;}}
        '''
      )
    ),
    HTML.html("body")(*content)
  )

def code (): return page(

  script(f'''
  let body = document.body;
  let terminal = document.createElement('div');
  body.appendChild(terminal);
  let input = document.createElement('input');
  input.id = 'input';
  input.style.border = 'none';
  input.placeholder = '>>';
  body.appendChild(input);

  input.addEventListener('keydown', (event) => {{
    if (event.key === 'Enter') {{
      if (input.value) fetch(`/exec/${{input.value}}`)
      input.value = '';
    }}
  }});
  let log_count = 0;
  let version = {check};
  function add_log(index) {{
    let line = document.createElement('p');
    terminal.appendChild(line);
    fetch(`/log/${{index}}`).then(response => response.text()).then(data => line.innerHTML = data);
  }}

  setInterval(() => {{
    fetch('/status').then(response => response.json()).then(data => {{
      ({{version: new_version, log_count: new_log_count}} = data);
      if (version != new_version){{
        window.location.reload();
      }}
      while (log_count < new_log_count) {{
        add_log(log_count);
        log_count++;
      }}
    }});
  }}, 100);
''')).code()

def log(message): out.append(message)
def view(idx: int)->str:
  item = out[idx]
  h = item
  if isinstance(item, HTML): h = item
  elif isinstance(item, str): h = item
  else: h = repr(item)
  return p(span(f"out[{idx}]: ", style="color: #888;"), h).code()

def get_logs(): return out
def clear():
  global check
  out.clear()
  check += 1

log(button("log", onclick="console.log('log')"))

class Foo:
  def __init__(self):
    print("Foo.__init__")
  def __view__(self): return "foo"
  def __repr__(self): return "Foo()"
log(Foo())


class Handler(BaseHTTPRequestHandler):    
  def do_GET(self):
    path = self.path.strip()
    if (path == "/logs"): self.respond("LOGS: " + "\n".join(out))
    elif (path.startswith("/log/")):
      self.respond(view(int(path.split("/log/")[1].split("/")[0])))
    elif (path == "/status"): self.respond(json.dumps({"version": check, "log_count": len(out)}))
    elif (path.startswith("/exec/")):
      cmd = path.split("/exec/")[1].split("/")[0]
      log(">>" + cmd)
      try: res = eval(cmd)
      except Exception as e: res = str(e)
      log(res)
      self.respond("")
    elif (path == "/"): self.respond(code())
    else: self.respond(f"not found: '{path}'")
  
  def respond(self, message: str):
    self.send_response(200)
    self.send_header("Content-Type", "text/html")
    self.end_headers()
    self.wfile.write(message.encode())

if __name__ == "__main__":
  print("starting server on port 8000")


  HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
