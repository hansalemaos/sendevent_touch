# Send touch/longtouch events to BlueStacks/Android


```python
$pip install sendevent-touch

from sendevent_touch import SendEventTouch

sendtouch = SendEventTouch(
    adb_path="C:\\Users\\Gamer\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
    deviceserial="localhost:5735",
    sdcard="/storage/emulated/0/",  # it is probably better to pass the path, not the symlink
    tmp_folder_on_sd_card="AUTOMAT",  # if the folder doesn't exist, it will be created
    bluestacks_divider=32767,
    use_bluestacks_coordinates=True,  # Recalculates the BlueStacks coordinates https://stackoverflow.com/a/73733261/15096247
)

sendtouch.connect_to_adb()

# Useful if you want to repeat the click
df_click1 = sendtouch.get_dataframe_for_clicks(50, 50)
sendtouch.touch_df(
    df_click1, struct_folder="struct real"
)  # "struct real" will use the recalculated coordinates for BlueStacks


# Touching without returning a DataFrame
sendtouch.touch(520, 40, struct_folder="struct real")


# Same thing for longtouch, duration is in seconds
sendtouch.longtouch_df(df_click1, duration=2.5, struct_folder="struct real")
sendtouch.longtouch(520, 40, duration=3.1, struct_folder="struct real")


# Using struct_folder="struct" should work for any rooted Android device, but I haven't checked it!
# I would be grateful for any feedback!
df_click1 = sendtouch.get_dataframe_for_clicks(50, 50)
sendtouch.touch_df(df_click1, struct_folder="struct")
sendtouch.touch(520, 40, struct_folder="struct")


sendtouch.longtouch_df(df_click1, duration=2, struct_folder="struct")
sendtouch.longtouch(520, 40, duration=3, struct_folder="struct")

#%timeit sendtouch.touch_df(df_click1 ,struct_folder="struct real")
# 109 ms ± 4.62 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
#%timeit subprocess.run('adb shell input tap 50 50')
# 197 ms ± 1.54 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)

```

### Tested against Windows 10 / Python 3.9.13 / BlueStacks 5

It should also work with any rooted Android device, the only problem might be the "bluestacks_divider".
[https://stackoverflow.com/a/73733261/15096247]()

But changing the code (if necessary) shouldn't be a big thing. 
Since my cell phone is not rooted, and I have no intention of rooting it, I cannot test the module against a physical Android device. (I would be grateful for any feedback)

