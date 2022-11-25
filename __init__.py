import os
import struct
import subprocess
import tempfile
from functools import partial

import psutil
import regex
import pandas as pd
import numpy as np
from touchtouch import touch
import keyboard as keyboard__

arred = lambda x, n: x * (10 ** n) // 1 / (10 ** n)


def get_tmpfile(suffix=".txt"):
    tfp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    filename = tfp.name
    filename = os.path.normpath(filename)
    tfp.close()
    return filename, partial(os.remove, tfp.name)


def execute_adb_command(
    cmd: str, subcommands: list, exit_keys: str = "ctrl+x", end_of_printline: str = ""
) -> list:
    if isinstance(subcommands, str):
        subcommands = [subcommands]
    elif isinstance(subcommands, tuple):
        subcommands = list(subcommands)
    popen = None

    def run_subprocess(cmd):
        nonlocal popen

        def kill_process():
            nonlocal popen
            try:
                print("Killing the process")
                p = psutil.Process(popen.pid)
                p.kill()
                try:
                    if exit_keys in keyboard__.__dict__["_hotkeys"]:
                        keyboard__.remove_hotkey(exit_keys)
                except Exception:
                    try:
                        keyboard__.unhook_all_hotkeys()
                    except Exception:
                        pass
            except Exception:
                try:
                    keyboard__.unhook_all_hotkeys()
                except Exception:
                    pass

        if exit_keys not in keyboard__.__dict__["_hotkeys"]:
            keyboard__.add_hotkey(exit_keys, kill_process)

        DEVNULL = open(os.devnull, "wb")
        try:
            popen = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=True,
                stderr=DEVNULL,
                shell=False,
            )

            for subcommand in subcommands:
                if isinstance(subcommand, bytes):
                    subcommand = subcommand.rstrip(b"\n") + b"\n"

                    subcommand = subcommand.decode("utf-8", "replace")
                else:
                    subcommand = subcommand.rstrip("\n") + "\n"

                popen.stdin.write(subcommand)

            popen.stdin.close()

            for stdout_line in iter(popen.stdout.readline, ""):
                try:
                    yield stdout_line
                except Exception as Fehler:
                    continue
            popen.stdout.close()
            return_code = popen.wait()
        except Exception as Fehler:
            # print(Fehler)
            try:
                popen.stdout.close()
                return_code = popen.wait()
            except Exception as Fehler:
                yield ""

    proxyresults = []
    try:
        for proxyresult in run_subprocess(cmd):
            proxyresults.append(proxyresult)
            print(proxyresult, end=end_of_printline)
    except KeyboardInterrupt:
        try:
            p = psutil.Process(popen.pid)
            p.kill()
            popen = None
        except Exception as da:
            pass
            # print(da)

    try:
        if popen is not None:
            p = psutil.Process(popen.pid)
            p.kill()
    except Exception as da:
        pass

    try:
        if exit_keys in keyboard__.__dict__["_hotkeys"]:
            keyboard__.remove_hotkey(exit_keys)
    except Exception:
        try:
            keyboard__.unhook_all_hotkeys()
        except Exception:
            pass
    return proxyresults


def adb_path_exists(adb_path, deviceserial, path):
    ex = (
        subprocess.run(
            f"""{adb_path} -s {deviceserial} shell ls {path} > /dev/null 2>&1 && echo "True" || echo "False""",
            shell=False,
            capture_output=True,
        )
        .stdout.decode("utf-8", "ignore")
        .strip()
    )

    if ex == "False":
        return False
    return True


def copy_bin_files_to_hdd(filepath, data):
    touch(filepath)
    try:
        with open(filepath, mode="wb") as f:
            f.write(data)
        return True
    except Exception:
        pass
    return False


def execute_click_sendevent(
    df, adb_path, deviceserial, sdcard, structfolder="struct real"
):
    df2 = df

    if structfolder == "struct real":
        if not adb_path_exists(
            adb_path, deviceserial, df2.struct_real_file_android.iloc[0]
        ):
            copy_bin_files_to_hdd(
                df2.struct_real_filename.iloc[0], df2.aa_struct_real_together.iloc[0]
            )
            subprocess.run(
                fr"{adb_path} -s {deviceserial} push {df2.struct_real_filename.iloc[0]} {sdcard}"
            )
        execute_adb_command(
            f"{adb_path} -s {deviceserial} shell",
            [f"{df2.struct_real_copy_dv.iloc[0]}\nexit"],
        )

    else:
        if not adb_path_exists(adb_path, deviceserial, df2.struct_file_android.iloc[0]):

            copy_bin_files_to_hdd(
                df2.struct_filename.iloc[0], df2.aa_struct_together.iloc[0]
            )

            subprocess.run(
                fr"{adb_path} -s {deviceserial} push {df2.struct_filename.iloc[0]} {sdcard}"
            )
        execute_adb_command(
            f"{adb_path} -s {deviceserial} shell",
            [f"{df2.struct_copy_dv.iloc[0]}\nexit"],
        )


def execute_click_sendevent_duration(
    df, duration, adb_path, deviceserial, sdcard, structfolder="struct real"
):
    clickevent, removelickevent = get_tmpfile(suffix=".bin")
    clickevent2, removelickevent2 = get_tmpfile(suffix=".bin")

    if structfolder == "struct real":
        with open(clickevent, mode="wb") as f:
            f.write(df.aa_struct_real_together.iloc[0][:48])
        with open(clickevent2, mode="wb") as f:
            f.write(df.aa_struct_real_together.iloc[0][48:])
        secondlen = len(df.aa_struct_real_together.iloc[0][48:])
    else:
        with open(clickevent, mode="wb") as f:
            f.write(df.aa_struct_together.iloc[0][:48])
        with open(clickevent2, mode="wb") as f:
            f.write(df.aa_struct_together.iloc[0][48:])
        secondlen = len(df.aa_struct_together.iloc[0][48:])

    subprocess.run(f"{adb_path} -s {deviceserial} push {clickevent} {sdcard}")
    subprocess.run(f"{adb_path} -s {deviceserial} push {clickevent2} {sdcard}")
    clickeventfilepure = clickevent.split(os.sep)[-1]
    clickeventfilepure2 = clickevent2.split(os.sep)[-1]
    execute_adb_command(
        cmd=f"{adb_path} -s {deviceserial} shell",
        subcommands=[
            f"dd bs=48 if={sdcard}{clickeventfilepure} of={df.aa_device.iloc[0]}\nsleep {arred(duration,4)}\ndd bs={secondlen} if={sdcard}{clickeventfilepure2} of={df.aa_device.iloc[0]}\nexit"
        ],
    )
    removelickevent()
    removelickevent2()


def get_click_dataframe(
    x,
    y,
    screenwidth,
    screenheight,
    sdcard="/storage/emulated/0/",
    bluestacks_divider=32767,
):

    coordsx = x
    coordsy = y

    basd = f"""[    15145.001801] /dev/input/event5: 3 53 {coordsx}
    [    15145.002801] /dev/input/event5: 3 54 {coordsy}
    [    15145.003801] /dev/input/event5: 0 0 0
    [    15145.004801] /dev/input/event5: 0 2 0
    [    15145.005801] /dev/input/event5: 0 0 0
    [    15145.006801] /dev/input/event5: 0 2 0
    [    15145.007801] /dev/input/event5: 0 0 0
    [    15145.008801] /dev/input/event5: 0 0 0


    """.strip().splitlines()

    allcommands = [k.strip() for k in basd]

    df2 = (
        pd.DataFrame(
            [
                regex.split(r"[\]:]?\s+", x.lstrip("[").strip())
                for x in allcommands
                if x.startswith("[ ")
            ],
            dtype="string",
        )
        .dropna()
        .reset_index(drop=True)
    )
    df2.columns = ["aa_time", "aa_device", "aa_type", "aa_code", "aa_value"]
    df2.aa_time = df2.aa_time.astype("string").astype("Float64")
    df2["aa_type_int"] = df2.aa_type.astype("string").astype(np.int32)
    df2["aa_code_int"] = df2.aa_code.astype("string").astype(np.int32)
    df2["aa_value_int"] = df2.aa_value.astype("string").astype(np.int32)

    df2.loc[:, "aa_real_coords"] = 0
    df2.loc[
        (df2.aa_value_int > 0) & (df2.aa_code_int == 53), "aa_real_coords"
    ] = coordsx
    df2.loc[
        (df2.aa_value_int > 0) & (df2.aa_code_int == 54), "aa_real_coords"
    ] = coordsy
    df2.loc[:, "aa_coords"] = 0

    df2.loc[(df2.aa_value_int > 0) & (df2.aa_code_int == 53), "aa_coords"] = int(
        df2.loc[(df2.aa_value_int > 0) & (df2.aa_code_int == 53), "aa_value_int"]
        * (bluestacks_divider / screenwidth)
    )
    df2.loc[(df2.aa_value_int > 0) & (df2.aa_code_int == 54), "aa_coords"] = int(
        df2.loc[(df2.aa_value_int > 0) & (df2.aa_code_int == 54), "aa_value_int"]
        * (bluestacks_divider / screenheight)
    )
    df2.loc[:, "aa_send_event"] = (
        "sendevent "
        + df2.aa_device
        + " "
        + df2.aa_type_int.astype("string")
        + " "
        + df2.aa_code_int.astype("string")
        + " "
        + df2.aa_value_int.astype("string")
    )
    df2.loc[:, "aa_send_event_real_ccords"] = (
        "sendevent "
        + df2.aa_device
        + " "
        + df2.aa_type_int.astype("string")
        + " "
        + df2.aa_code_int.astype("string")
        + " "
        + df2.aa_real_coords.astype("string")
    )
    FORMAT = "llHHI"
    EVENT_SIZE = struct.calcsize(FORMAT)

    df2["aa_struct_size"] = EVENT_SIZE * 8
    df2["aa_struct_real_size"] = EVENT_SIZE * 8

    df2.aa_value_int = df2.aa_value_int.astype(np.uint64)
    df2["aa_struct"] = df2.apply(
        lambda x: struct.pack(
            FORMAT, 0, 0, int(x.aa_type_int), int(x.aa_code_int), int(x.aa_value_int),
        ),
        axis=1,
    )
    df2["aa_struct_real"] = df2.apply(
        lambda x: struct.pack(
            FORMAT, 0, 0, int(x.aa_type_int), int(x.aa_code_int), int(x.aa_coords),
        ),
        axis=1,
    )
    df2.at[0, "aa_struct_together"] = b"".join(df2.aa_struct.to_list())
    df2.at[0, "aa_struct_real_together"] = b"".join(df2.aa_struct_real.to_list())
    clickevent, removelickevent = get_tmpfile(suffix=".bin")
    touch(clickevent)
    df2.at[0, "struct_filename"] = clickevent
    df2.at[0, "struct_fileremove"] = removelickevent
    clickevent2, removelickevent2 = get_tmpfile(suffix=".bin")
    touch(clickevent2)

    df2.at[0, "struct_real_filename"] = clickevent2
    df2.at[0, "struct_real_fileremove"] = removelickevent2
    dfgoa = df2[:1]
    df2.loc[dfgoa.index, "struct_copy_dv"] = dfgoa.apply(
        lambda x: f"dd bs={int(x.aa_struct_size)} if={sdcard}{x.struct_filename.split(os.sep)[-1]} of={x.aa_device}",
        axis=1,
    ).copy()
    df2.loc[dfgoa.index, "struct_real_copy_dv"] = dfgoa.apply(
        lambda x: f"dd bs={int(x.aa_struct_real_size)} if={sdcard}{x.struct_real_filename.split(os.sep)[-1]} of={x.aa_device}",
        axis=1,
    ).copy()
    df = df2.copy()
    df.loc[:, "struct_folder_android"] = regex.findall(
        r"(?<=if=).*?(?=/[^/]+\.bin\b)", df.struct_copy_dv.dropna().iloc[0]
    )[0]
    df.loc[:, "struct_real_folder_android"] = regex.findall(
        r"(?<=if=).*?(?=/[^/]+\.bin\b)", df.struct_real_copy_dv.dropna().iloc[0]
    )[0]

    extractstring = (
        df["struct_copy_dv"]
        .str.extract(r"(?<=if=)(?P<struct_file_android>.*?\.bin)\b")
        .copy()
    )
    df = pd.concat([df, extractstring], axis=1).copy()

    extractstring = (
        df["struct_real_copy_dv"]
        .str.extract(r"(?<=if=)(?P<struct_real_file_android>.*?\.bin)\b")
        .copy()
    )
    df = pd.concat([df, extractstring], axis=1).copy()
    return df


def connect_to_adb(adb_path, deviceserial):
    _ = subprocess.run(f"{adb_path} start-server", capture_output=True, shell=False)
    _ = subprocess.run(
        f"{adb_path} connect {deviceserial}", capture_output=True, shell=False
    )


def get_screenwidth(adb_path, deviceserial):
    screenwidth, screenheight = (
        subprocess.run(
            fr'{adb_path} -s {deviceserial} shell dumpsys window | grep cur= |tr -s " " | cut -d " " -f 4|cut -d "=" -f 2',
            shell=True,
            capture_output=True,
        )
        .stdout.decode("utf-8", "ignore")
        .strip()
        .split("x")
    )
    screenwidth, screenheight = int(screenwidth), int(screenheight)
    return screenwidth, screenheight


class SendEventTouch:
    def __init__(
        self,
        adb_path,
        deviceserial,
        sdcard="/storage/emulated/0/",
        tmp_folder_on_sd_card="AUTOMAT",
        bluestacks_divider=32767,
        use_bluestacks_coordinates=True,
    ):
        self.adb_path = adb_path
        self.deviceserial = deviceserial
        self.sdcard = sdcard
        self.original_sdcard = sdcard
        self.bluestacks_divider = bluestacks_divider
        self.tmp_folder_on_sd_card = tmp_folder_on_sd_card
        self.use_bluestacks_coordinates = use_bluestacks_coordinates
        if self.use_bluestacks_coordinates:
            self.struct_folder = "struct"
        else:
            self.struct_folder = "struct real"
        self._create_sd_card_path()
        self.width = 0
        self.height = 0

    def connect_to_adb(self):
        connect_to_adb(
            adb_path=self.adb_path, deviceserial=self.deviceserial,
        )
        return self

    def _create_sd_card_path(self):
        pathexits = (
            "/"
            + regex.sub(
                r"[\\/]+",
                "/",
                os.path.join(self.original_sdcard, self.tmp_folder_on_sd_card),
            ).strip("/")
            + "/"
        )
        self.sdcard = pathexits
        if not adb_path_exists(
            adb_path=self.adb_path, deviceserial=self.deviceserial, path=pathexits
        ):

            foldertocreate = os.path.normpath(
                os.path.join(os.getcwd(), self.tmp_folder_on_sd_card)
            )
            if not os.path.exists(foldertocreate):
                os.makedirs(foldertocreate)
            subprocess.run(
                f"{self.adb_path} -s {self.deviceserial} push {foldertocreate} {self.original_sdcard}"
            )

    def _get_width_height_of_screen(self):
        self.width, self.height = get_screenwidth(
            adb_path=self.adb_path, deviceserial=self.deviceserial
        )
        return self

    def get_dataframe_for_clicks(self, x, y):
        if self.width == 0 or self.height == 0:
            self._get_width_height_of_screen()
        return get_click_dataframe(
            x,
            y,
            screenwidth=self.width,
            screenheight=self.height,
            sdcard=self.sdcard,
            bluestacks_divider=self.bluestacks_divider,
        )

    def touch(self, x, y, struct_folder="struct real"):
        if struct_folder is None:
            struct_folder = self.struct_folder
        df = self.get_dataframe_for_clicks(x, y,)
        return execute_click_sendevent(
            df,
            adb_path=self.adb_path,
            deviceserial=self.deviceserial,
            sdcard=self.sdcard,
            structfolder=struct_folder,
        )

    def touch_df(self, df, struct_folder="struct real"):
        if struct_folder is None:
            struct_folder = self.struct_folder
        return execute_click_sendevent(
            df,
            adb_path=self.adb_path,
            deviceserial=self.deviceserial,
            sdcard=self.sdcard,
            structfolder=struct_folder,
        )

    def longtouch_df(self, df, duration=1.0, struct_folder="struct real"):
        if struct_folder is None:
            struct_folder = self.struct_folder
        return execute_click_sendevent_duration(
            df=df,
            duration=duration,
            adb_path=self.adb_path,
            deviceserial=self.deviceserial,
            sdcard=self.sdcard,
            structfolder=struct_folder,
        )

    def longtouch(self, x, y, duration=1.0, struct_folder="struct real"):
        if struct_folder is None:
            struct_folder = self.struct_folder

        df = self.get_dataframe_for_clicks(x, y)
        return execute_click_sendevent_duration(
            df=df,
            duration=duration,
            adb_path=self.adb_path,
            deviceserial=self.deviceserial,
            sdcard=self.sdcard,
            structfolder=struct_folder,
        )
