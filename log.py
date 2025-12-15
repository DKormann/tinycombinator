# from dataclasses import dataclass
# from http.server import BaseHTTPRequestHandler, HTTPServer
# import json
# import random
# from typing import Callable, Dict, Tuple, Union

# @dataclass
# class HTML:
#   tag: str
#   attrs: Dict[str, str]
#   content: Tuple[Union[str, "HTML"]]
#   def code(self):
#     attrs = " ".join([f"{k}=\"{v}\"" for k, v in self.attrs.items()])
#     content = "".join([item.code() if isinstance(item, HTML) else str(item) for item in self.content])
#     return f'''<{self.tag} {attrs}>{content}</{self.tag}>'''

#   @staticmethod
#   def html(tag: str):
#     def mk(*content: Union[str, "HTML"], **attrs: Dict[str, str]):
#       return HTML(tag=tag, attrs=attrs, content=content)
#     return mk


# @dataclass
# class Script: code: str


# p = HTML.html("p")
# h1 = HTML.html("h1")
# h2 = HTML.html("h2")
# h3 = HTML.html("h3")
# div = HTML.html("div")
# span = HTML.html("span")
# script = HTML.html("script")
# style = HTML.html("style")
# check = random.randint(0, 10_000)
# out = []


# def page(*content: HTML):
#   return HTML.html("html")(
#     HTML.html("head")(
#       style(
#         '''
#         body {
#           --background: #f0f0f0; --color: #000000;
#           color: var(--color);
#           background: var(--background);
#           font-family: monospace;
#         }

#         @media (prefers-color-scheme: dark) {body {--background: #000000; --color: #f0f0f0;}}
#         '''
#       )
#     ),
#     HTML.html("body")(*content)
#   )

# def code (): return page(

#   script(f'''
#   let body = document.body;
#   let terminal = document.createElement('div');
#   body.appendChild(terminal);
#   let input = document.createElement('input');
#   input.id = 'input';
#   input.style.border = 'none';
#   input.placeholder = '>>';
#   body.appendChild(input);
#   function pyexec(cmd) {{
#     fetch('/call', {{
#       method: 'POST',
#       body: cmd
#     }})
#     refresh();
#   }}
#   input.addEventListener('keydown', (event) => {{
#     if (event.key === 'Enter') {{
#       if (input.value) fetch('/exec', {{
#         method: 'POST',
#         body: input.value
#       }})
#       input.value = '';
#       refresh();
#     }}
#   }});


#   let log_count = 0;
#   let version = {check};
#   function add_log(index) {{
#     let line = document.createElement('p');
#     terminal.appendChild(line);
#     fetch(`/log/${{index}}`).then(response => response.json()).then(data => {{
#       line.innerHTML = `<span style="color: #888;">out[${{index}}]: </span>`;
#       let content = document.createElement('span');
#       line.appendChild(content);
#       content.innerHTML = data.html;
#       if (data.code) content.replaceWith((new Function(data.code))() ?? content);
#       }});
#   }}

#   let refresh = () => {{
#     fetch('/status').then(response => response.json()).then(data => {{
#       ({{version: new_version, log_count: new_log_count}} = data);
#       if (version != new_version){{
#         window.location.reload();
#       }}
#       while (log_count < new_log_count) {{
#         add_log(log_count);
#         log_count++;
#       }}
#     }});
#   }};

#   setInterval(refresh, 100);
# ''')).code()




# functions = {}

# def button(text: str, onclick: Callable)->HTML:
#   id = len(functions)
#   functions[id] = onclick
#   return HTML.html("button")(text, onclick=f"pyexec('functions[{id}]()')")


# def log(message): out.append(message)
# def view(idx: int)->str:
#   item = out[idx]
#   h = ""
#   if isinstance(item, HTML): h = item.code()
#   elif isinstance(item, Script): return json.dumps({"code": item.code})
#   elif isinstance(item, str): h = item
#   else: h = repr(item).replace("<", "&lt;").replace(">", "&gt;")
#   return json.dumps({"html": h, "code": None})

# def get_logs(): return out
# def clear():
#   global check
#   check += 1
#   out.clear()
#   functions.clear()

# log("h33llo")
# log(Script('''
# let d = document.createElement('span');
# d.innerHTML = 'hello';
# d.style.color = 'red';
# d.style.cursor = 'pointer';
# d.addEventListener('click', () => {{
#   console.log('clicked');
#   d.innerHTML = 'clicked';
# }});
# return d;
# '''))


# def pyeval(cmd: str):
#   try: res = eval(cmd)
#   except Exception as e: res = str(e)
#   return res

# class Handler(BaseHTTPRequestHandler):
#   def log_message(self, format, *args):
#     pass
    
#   def do_GET(self):
#     path = self.path.strip()
#     if (path == "/logs"): self.respond("LOGS: " + "\n".join(out))
#     elif (path.startswith("/log/")):
#       self.respond(view(int(path.split("/log/")[1].split("/")[0])))
#     elif (path == "/status"): self.respond(json.dumps({"version": check, "log_count": len(out)}))
#     elif (path == "/"):
#       self.respond(code())
#     else: self.respond(f"not found: '{path}'")
  
#   def do_POST(self):
#     path = self.path.strip()
#     if (path == "/call"):
#       cmd = self.rfile.read(int(self.headers.get("Content-Length"))).decode()
#       pyeval(cmd)
#       self.respond("")
#     if (path == "/exec"):
#       cmd = self.rfile.read(int(self.headers.get("Content-Length"))).decode()
#       log("$ " + cmd)
#       log(pyeval(cmd))
#       self.respond("")
  
#   def respond(self, message: str):
#     self.send_response(200)
#     self.send_header("Content-Type", "text/html")
#     self.end_headers()
#     self.wfile.write(message.encode())

# if __name__ == "__main__":
#   HTTPServer(
#     ("0.0.0.0", 8000),
#     Handler
#   ).serve_forever()

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import random
from typing import Callable, Dict, Union

def html(tag: str):
  def mk(*content: str, **attrs: Dict[str, str]):
    attrs = "\n".join([f"el.{key} = '{json.dumps(v)}';" for key, v in attrs.items()])
    content = ''.join(content).replace("\\", "\\\\").replace("\n", "\\n").replace("'", "\\'")

    return f'''(()=>{{
      let el = document.createElement("{tag}");
      el.innerHTML = '{content}';
      {attrs}
      return el
    }})()'''
  return mk

h2 = html("h2")
script = html("script")
style = html("style")
body = html("body")
head = html("head")
div = html("div")
span = html("span")
p = html("p")
pre = html("pre")
out = []

version = random.randint(0, 1000000)

page = f'''
<html>
<head><style>body {{
  --background: #f0f0f0; --color: #000000;
  @media (prefers-color-scheme: dark) {{body {{--background: #000000; --color: #000000;}}}}
  color: var(--color);
  background: var(--background);
  font-family: monospace;
}}</style></head>
<body>

  <script>
    let version = {version};
    let log_count = 0;
    async function python(cmd){{
      let ret = await fetch("/call", {{method: "POST", body: cmd}}).then(response => response.text());
      console.log(ret);
      return (new Function("return " + ret))()
    }};
    let term = document.createElement("div");
    document.body.appendChild(term);

    function add_log(index){{
      let line = document.createElement("p");
      term.appendChild(line);
      python(`out[${{index}}]`).then(res => line.replaceWith(res))
    }}

    function refresh(){{
      fetch("/status").then(response => response.json()).then(async data => {{
        if (version != data.version) window.location.reload();
        while (log_count < data.log_count) {{
          add_log(log_count);
          log_count++;
        }}
      }})
    }}
    setInterval(refresh, 100);
  </script>
</body></html>'''


def clear():
  out.clear()
  global version
  version = random.randint(0, 1000000)

functions = {}
def log(message):
  if isinstance(message, int): message = str(message)
  elif isinstance(message, list):
    message = "".join([pre(item) for item in message])
    p = pre(message)
    
  out.append(pre(message))


def meep(): return p("meepooo")

def call(fn: Callable, *args: str):
  id = len(functions)
  functions[id] = fn
  return f'python(`functions[{id}]({", ".join(args)})`)'


def button(text: str, onclick: Callable):

  return f'''(()=>{{
    let but = document.createElement("button");
    but.innerHTML = "{text}";
    but.addEventListener("click", () => {{
      {call(onclick)}
    }});
    return but;
  }})()'''

out.append(button("Click me", lambda: log("clicked")))




class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
    if (self.path == "/status"): self.respond(json.dumps({"version": version, "log_count": len(out)}))
    else: self.respond(page)
  
  def do_POST(self):
    if (self.path == "/call"):
      cmd = self.rfile.read(int(self.headers.get("Content-Length"))).decode()
      self.respond(eval(cmd))

  def respond(self, message: str):
    self.send_response(200)
    self.send_header("Content-Type", f"text/html")
    self.end_headers()
    self.wfile.write(message.encode())


if __name__ == "__main__":
  HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()


