from zipapp import create_archive
import uiautomator2
from random import uniform
from typing import Optional
from enum import Enum, unique
from gettext import find
from os import listdir
from re import search

from insomniac.sleeper import sleeper
from insomniac.utils import *

UI_TIMEOUT_LONG = 5
UI_TIMEOUT_SHORT = 1

device = uiautomator2.connect()


class DeviceFacade:
    deviceV2 = None  # uiautomator2
    width = None
    height = None
    device_id = None
    app_id = None
    typewriter = None

    def __init__(self, device_id, app_id, typewriter):
        self.device_id = device_id
        self.app_id = app_id
        self.typewriter = typewriter

        try:
            self.deviceV2 = uiautomator2.connect(
            ) if device_id is None else uiautomator2.connect(device_id)
        except ImportError:
            raise ImportError(
                "Please install uiautomator2: pip3 install uiautomator2")

    def find(self, *args, **kwargs):
        try:
            # print(self.deviceV2, args, kwargs)
            view = self.deviceV2(*args, **kwargs)
        except uiautomator2.JSONRPCError as e:
            raise DeviceFacade.JsonRpcError(e)
        return DeviceFacade.View(is_old=False, view=view, device=self)

    class View:
        device = None
        viewV1 = None  # uiautomator
        viewV2 = None  # uiautomator2

        def __init__(self, is_old, view, device):
            self.device = device
            if is_old:
                self.viewV1 = view
            else:
                self.viewV2 = view

        def __iter__(self):
            children = []
            try:
                for item in self.viewV2:
                    children.append(DeviceFacade.View(
                        is_old=False, view=item, device=self.device))
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return iter(children)

        def child(self, *args, **kwargs):
            try:
                view = self.viewV2.child(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(is_old=False, view=view, device=self.device)

        def right(self, *args, **kwargs) -> Optional['DeviceFacade.View']:
            try:
                view = self.viewV2.right(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(is_old=False, view=view, device=self.device)

        def left(self, *args, **kwargs):
            try:
                view = self.viewV2.left(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(is_old=False, view=view, device=self.device)

        def up(self, *args, **kwargs):
            try:
                view = self.viewV2.up(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(is_old=False, view=view, device=self.device)

        def down(self, *args, **kwargs):
            try:
                view = self.viewV2.down(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(is_old=False, view=view, device=self.device)

        def click(self, mode=None, ignore_if_missing=False):
            if ignore_if_missing and not self.exists(quick=True):
                return

            mode = DeviceFacade.Place.WHOLE if mode is None else mode
            if mode == DeviceFacade.Place.WHOLE:
                x_offset = uniform(0.15, 0.85)
                y_offset = uniform(0.15, 0.85)

            elif mode == DeviceFacade.Place.LEFT:
                x_offset = uniform(0.15, 0.4)
                y_offset = uniform(0.15, 0.85)

            elif mode == DeviceFacade.Place.CENTER:
                x_offset = uniform(0.4, 0.6)
                y_offset = uniform(0.15, 0.85)

            elif mode == DeviceFacade.Place.RIGHT:
                x_offset = uniform(0.6, 0.85)
                y_offset = uniform(0.15, 0.85)

            else:
                x_offset = 0.5
                y_offset = 0.5

            if self.viewV1 is not None:
                import uiautomator
                try:
                    self.viewV1.click.wait()
                except uiautomator.JsonRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)
            else:
                import uiautomator2
                try:
                    self.viewV2.click(
                        UI_TIMEOUT_LONG, offset=(x_offset, y_offset))
                except uiautomator2.JSONRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)

        def long_click(self):
            if self.viewV1 is not None:
                import uiautomator
                try:
                    self.viewV1.long_click()
                except uiautomator.JsonRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)
            else:
                import uiautomator2
                try:
                    self.viewV2.long_click()
                except uiautomator2.JSONRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)

        def double_click(self, padding=0.3):
            """
            Double click randomly in the selected view using padding
            padding: % of how far from the borders we want the double click to happen.
            """

            if self.viewV1 is not None:
                self._double_click_v1()
            else:
                self._double_click_v2(padding)

        def scroll(self, direction):
            if self.viewV1 is not None:
                import uiautomator
                try:
                    if direction == DeviceFacade.Direction.TOP:
                        self.viewV1.scroll.toBeginning(max_swipes=1)
                    else:
                        self.viewV1.scroll.toEnd(max_swipes=1)
                except uiautomator.JsonRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)
            else:
                import uiautomator2
                try:
                    if direction == DeviceFacade.Direction.TOP:
                        self.viewV2.scroll.toBeginning(max_swipes=1)
                    else:
                        self.viewV2.scroll.toEnd(max_swipes=1)
                except uiautomator2.JSONRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)

        def swipe(self, direction):
            if self.viewV1 is not None:
                import uiautomator
                try:
                    if direction == DeviceFacade.Direction.TOP:
                        self.viewV1.fling.toBeginning(max_swipes=5)
                    else:
                        self.viewV1.fling.toEnd(max_swipes=5)
                except uiautomator.JsonRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)
            else:
                import uiautomator2
                try:
                    if direction == DeviceFacade.Direction.TOP:
                        self.viewV2.fling.toBeginning(max_swipes=5)
                    else:
                        self.viewV2.fling.toEnd(max_swipes=5)
                except uiautomator2.JSONRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)

        def exists(self, quick=False):
            try:
                return self.viewV2.exists(UI_TIMEOUT_SHORT if quick else UI_TIMEOUT_LONG)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def wait(self):
            try:
                return self.viewV2.wait(timeout=UI_TIMEOUT_LONG)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def get_bounds(self):
            try:
                return self.viewV2.info['bounds']
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def get_text(self, retry=True):
            max_attempts = 1 if not retry else 3
            attempts = 0
            while attempts < max_attempts:
                attempts += 1
                try:
                    text = self.viewV2.info['text']
                    if text is None:
                        if attempts < max_attempts:
                            print("Could not get text. "
                                  "Waiting 2 seconds and trying again...")
                            sleep(2)  # wait 2 seconds and retry
                            continue
                    else:
                        return text
                except uiautomator2.JSONRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)

            print(f"Attempted to get text {attempts} times. You may have a slow network or are "
                  f"experiencing another problem.")
            return ""

        def get_selected(self) -> bool:
            import uiautomator2
            try:
                return self.viewV2.info["selected"]
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def is_enabled(self) -> bool:
            if self.viewV1 is not None:
                import uiautomator
                try:
                    self.viewV1.info["enabled"]
                except uiautomator.JsonRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)
            else:
                import uiautomator2
                try:
                    return self.viewV2.info["enabled"]
                except uiautomator2.JSONRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)

        def is_focused(self) -> bool:
            if self.viewV1 is not None:
                import uiautomator
                try:
                    self.viewV1.info["focused"]
                except uiautomator.JsonRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)
            else:
                import uiautomator2
                try:
                    return self.viewV2.info["focused"]
                except uiautomator2.JSONRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)

        def set_text(self, text):
            if self.device.typewriter is not None and self.device.typewriter.write(self, text):
                return
            if self.viewV1 is not None:
                import uiautomator
                try:
                    self.viewV1.set_text(text)
                except uiautomator.JsonRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)
            else:
                import uiautomator2
                try:
                    self.viewV2.set_text(text)
                except uiautomator2.JSONRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)

        def _double_click_v1(self):
            import uiautomator
            config = self.device.deviceV1.server.jsonrpc.getConfigurator()
            config['actionAcknowledgmentTimeout'] = 40
            self.device.deviceV1.server.jsonrpc.setConfigurator(config)
            try:
                self.viewV1.click()
                self.viewV1.click()
            except uiautomator.JsonRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            config['actionAcknowledgmentTimeout'] = 3000
            self.device.deviceV1.server.jsonrpc.setConfigurator(config)

        def _double_click_v2(self, padding):
            visible_bounds = self.get_bounds()
            horizontal_len = visible_bounds["right"] - visible_bounds["left"]
            vertical_len = visible_bounds["bottom"] - visible_bounds["top"]
            horizintal_padding = int(padding * horizontal_len)
            vertical_padding = int(padding * vertical_len)
            random_x = int(
                uniform(
                    visible_bounds["left"] + horizintal_padding,
                    visible_bounds["right"] - horizintal_padding,
                )
            )
            random_y = int(
                uniform(
                    visible_bounds["top"] + vertical_padding,
                    visible_bounds["bottom"] - vertical_padding,
                )
            )
            time_between_clicks = uniform(0.050, 0.200)
            try:
                self.device.deviceV2.double_click(
                    random_x, random_y, duration=time_between_clicks)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

    @unique
    class Direction(Enum):
        TOP = 0
        BOTTOM = 1
        RIGHT = 2
        LEFT = 3

    @unique
    class Place(Enum):
        # TODO: add more places
        RIGHT = 0
        WHOLE = 1
        CENTER = 2
        BOTTOM = 3
        LEFT = 4


def open_instagram():
    device_id = None
    app_id = 'com.instagram.android'
    print("Open Instagram app")
    cmd = ("adb" + ("" if device_id is None else " -s " + device_id) +
           f" shell am start -n {app_id}/com.instagram.mainactivity.MainActivity")

    cmd_res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE,
                             shell=True, encoding="utf8")
    err = cmd_res.stderr.strip()
    if err:
        if err == APP_REOPEN_WARNING:
            print('HAHA BICH')
        else:
            print(COLOR_FAIL + err + COLOR_ENDC)


open_instagram()


dev1 = DeviceFacade(None, 'com.instagram.android', None)


create_account_button = dev1.find(resourceId="com.instagram.android:id/sign_up_with_email_or_phone",
                                  className='android.widget.Button')

create_account_button.click()
