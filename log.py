from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import random
from typing import Callable, List, Union

version = random.randint(0, 1000000)
page = '''<html>

<head>
  <style>
  body {
    --background: #f0f0f0; --color: #000000;
    color: var(--color);
    background: var(--background);
    font-family: monospace;
  }
  @media (prefers-color-scheme: dark) {body {--background: #000000; --color: #f0f0f0;}}
  </style>
</head>
<body>
</body>
  <script>
  let body = document.body;
  let terminal = document.createElement('div');
  body.appendChild(terminal);
  let input = document.createElement('input');
  input.id = 'input';
  input.style.border = 'none';
  input.placeholder = '>>';
  body.appendChild(input);
  let log_count = 0;
  let version = 0;
  function add_log(index){
    let line = document.createElement('p');
    terminal.appendChild(line);
    fetch(`/log/${index}`).then(response => response.text()).then(data => {
      line.innerHTML = `<span style="color: #888;">out[${index}]: </span>`;
      let content = document.createElement('span');
      line.appendChild(content);

      content.innerHTML = data;
      line.addEventListener('click', (e) => {
        console.log("CLICK:", e.target)
        let target = e.target;
        while (!target.id) target = target.parentElement;
        fetch(`/click/${index}/${target.id}`)
        .then(response=>response.text()).then(data=>{content.innerHTML = data})
      })
    });
  }
  function refresh(){
    fetch('/status').then(response => response.json()).then(data => {
      ({version: new_version, log_count: new_log_count} = data);
      if (version != new_version){
        window.location.reload();
      }
      while (log_count < new_log_count) {
        add_log(log_count);
        log_count++;
      }
    });
  }
  function call(cmd){
    fetch('/call', {method: 'POST', body: cmd}).then(()=>refresh())
  }
  let histindex = 0;
  let history = [];
  input.addEventListener('keydown', (e) => {
    if (e.key == 'Enter') {
      call(input.value);
      history.push(input.value);
      input.value = '';
    }
    if (e.key == 'ArrowUp' && histindex < history.length -1) {
      histindex++;
      input.value = history[history.length - histindex];
    }else if (e.key == 'ArrowDown' && histindex > 1) {
      histindex--;
      input.value = history[history.length - histindex];
    }else histindex = 0;
    if (e.key == 'k' && e.metaKey) call('clear()');
  });

  fetch('/status').then(response => response.json()).then(data => {
    version = data.version
    setInterval(refresh, 100);
  });

  input.focus()
  </script>
<html>'''


def style(**kwargs): return "; ".join(map(lambda x: f"{x[0]}: {x[1]}", kwargs.items()))

def html(tag: str):
  def mk(content: str, style: str = None, id: str = None):
    id = f" id=\"{id}\"" if id else ''
    style = f" style=\"{style}\"" if style else ''
    return f"<{tag}{id}{style}>{content}</{tag}>"
  return mk

p = html("p")
span = html("span")
div = html("div")


class Item:
  def __init__(self, data: any, id = "0"):
    self.data = data
    self.content = ""
    self.open = False
    self.id = id
    self.children : List[Item] = []
    self.render()

  def onclick(self, target: str):
    if (target == self.id): self.set_open( not self.open)
    else:
      for child in self.children:
        if (target.startswith(child.id)): child.onclick(target)

  def set_open(item, open: bool):
    if (item.open == open): return
    item.open = open
    item.children = [Item(x, f"{item.id}.{i}") for i, x in enumerate(item.data)]if isinstance(item.data, list) else []

  def render(item):
    for child in item.children:
      child.render()
    if (item.open):
      if isinstance(item.data, list):
        item.content = span("[" + "".join([div(x.content, style( margin="0 0 0 20px")) for x in item.children]) + "]", id=item.id)
    else: item.content = span(str(item.data).replace("<", "&lt;").replace(">", "&gt;"), style(cursor="pointer"), id=item.id)


out:list = []
items = []

def log(x:any):
  out.append(x)
  items.append(Item(x))

log([1,[2,[3,4]]])
def add(a,b): return a + b
log(add)

def clear():
  out.clear()
  items.clear()
  global version
  version = random.randint(0, 1000000)


# def view(x:list, bars:bool = False):

context = {"log": log, "out": out, "clear": clear}

class Handler(BaseHTTPRequestHandler):
  def log_message(self, format, *args): pass
  def do_GET(self):
    if (self.path == "/status"): self.respond(json.dumps({"version": version, "log_count": len(items)}))
    elif (self.path.startswith("/log/")):
      index = int(self.path.split("/log/")[1])
      self.respond(items[index].content)
    elif (self.path == "/"): self.respond(page)
    elif (self.path.startswith("/click/")):
      [index, target] = self.path.split("/click/")[1].split("/")
      index = int(index)
      if items[index].onclick:
        items[index].onclick(target)
        items[index].render()
        self.respond(items[index].content)
    else: self.respond(f"not found: '{self.path}'")
  
  def do_POST(self):
    if (self.path == "/call"):
      cmd = self.rfile.read(int(self.headers.get("Content-Length"))).decode()
      try:
        log("$ " + cmd)
        res = eval(cmd, context)
        if res is not None: log(res)
      except Exception as e: log(e)
      self.respond("ok")

  def respond(self, message: str):
    self.send_response(200)
    self.send_header("Content-Type", f"text/html")
    self.send_header("Access-Control-Allow-Origin", "*")
    self.end_headers()
    self.wfile.write(message.encode())

if __name__ == "__main__":
  HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
