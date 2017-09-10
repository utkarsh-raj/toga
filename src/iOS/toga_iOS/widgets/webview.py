from rubicon.objc import objc_method
from .base import Widget
from ..libs import *


class TogaWebView(UIWebView):
    @objc_method
    def webView_didFinishLoadForFrame_(self, sender, frame) -> None:
        # print ("FINISHED LOADING")
        pass

    @objc_method
    def acceptsFirstResponder(self) -> bool:
        return True

    @objc_method
    def keyDown_(self, event) -> None:
        if self.interface.on_key_down:
            self.interface.on_key_down(event.keyCode, event.modifierFlags)


class WebView(Widget):
    def create(self):
        self.native = TogaWebView.alloc().init()
        self.native.interface = self.interface
        self.native.delegate = self.native

        # Add the layout constraints
        self.add_constraints()

    def set_url(self, value):
        if value:
            request = NSURLRequest.requestWithURL_(NSURL.URLWithString_(self.interface.url))
            self.native.loadRequest_(request)

    def set_user_agent(self, value):
        # self.native.???? = value if value else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8"
        pass

    def set_content(self, root_url, content):
        self.native.loadHTMLString_baseURL_(content, NSURL.URLWithString_(root_url))

    def evaluate(self, javascript):
        return self.native.stringByEvaluatingJavaScriptFromString_(javascript)

    def set_user_agent(self, value):
        pass
