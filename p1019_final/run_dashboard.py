import http.server
import os
import socketserver
import webbrowser

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, directory=DIRECTORY, **kwargs)


print(f"🚀 대시보드 서버가 시작되었습니다: http://localhost:{PORT}")
webbrowser.open(f"http://localhost:{PORT}/dashboard.html")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    print("\n서버를 종료합니다.")