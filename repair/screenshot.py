import pyautogui

# Take screenshot
pic = pyautogui.screenshot()

# Save the image
pic.save('/home/circleci/project/tmp/screenshots/error.png')