import os
import subprocess
import sys

from SimpleHTTPServer import SimpleHTTPRequestHandler
import SocketServer


PORT = 8000

# insane
shelf = None

class ToolshelfServeHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global shelf

        contents = '<ul>'

        specs = shelf.expand_docked_specs(['all'])
        sources = shelf.make_sources_from_specs(specs)
        for source in sources:
            contents += '<li>{0}</li>\n'.format(source.name)
        
        contents += '</ul>'
        
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        page = """
<html>
<h1>toolshelf: <code>{0}</code></h1>
{1}
</html>
""".format(shelf.dir, contents)
        self.wfile.write(page)


def serve(local_shelf, args):
    global shelf
    shelf = local_shelf
    httpd = SocketServer.TCPServer(("", PORT), ToolshelfServeHandler)
    httpd.serve_forever()
