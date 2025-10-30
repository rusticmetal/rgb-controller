# Instructions for setting up startup functionality :

(this might eventually be part of the main program, but has to be done manually right now)

There are two methods of enabling startup functionality, and from what I have tested so far, option #1 will not run the program as Administrator, so
any time the computer sleeps and then wakes up, the patterns will not resume (though they can still be manually loaded after wakeup).

Option #2 displays patterns and correctly restarts device patterns after the computer wakes, however requires Administrator privileges for the application, and to set
some tasks in the Task Scheduler, though with this method you can set it and forget it.

# Option #1 (patterns will not load after wakeup)

1. In run_RGB.bat, change the path to where your program executable lies.

2. Additionally, you can change the timeout to a greater value if you think that the startup APIs cannot load before the RGB Controller.
If the RGB Controller loads first, some of your patterns might not appear and might have to be manually set, so try experimenting with a value you find optimal.

3. Finally, go to your Startup Apps in Windows, and make a new shortcut to run_RGB.bat.

# Option #2 (patterns load after wakeup, requires Administrator privileges)

1. run_RGB_once.bat

First, edit the path of RGB_boot_flag.txt inside of this file if you care about where the temp file is generated. What this file does is that it
ensures that the program only runs once after the first logon after booting (it is deleted after loading the program).

Next, change the FLAG path to where your program executable lies.

Additionally, you can change the timeout to a greater value if you think that the startup APIs cannot load before the RGB Controller.
If the RGB Controller loads first, some of your patterns might not appear and might have to be manually set, so try experimenting with a value you find optimal.

2. set_RGB_flag_startup.bat

Change the location of RGB_boot_flag.txt to whatever you set it as in run_RGB_once.bat.

3. Open Task Scheduler on your computer, and do the following:

Click 'Create Task' and name it 'RGB Boot Flag' (or whatever you want)
Configure it for your Windows Version, and select 'Run whether user is logged in or not'.
Select 'Run with highest privileges' if the path of RGB_boot_flag.txt is one where admin rights is needed (this is likely since this task is ran before user logon).
Add a Trigger for 'On system startup'.
Add an action, and browse your computer for the program to select the location of 'set_RGB_flag_startup.bat' that we just set up.

The flag should now be created whenever the system boots up.

Click 'Create Task' again and name it 'RGB First Logon' (or whatever you want)
Configure it for your Windows Version, and select 'Run only when the user is logged in'.
Select 'Run with highest privileges' if you care about patterns resuming after your computer wakes from sleep.
Add a Trigger 'On workstation unlock' or 'On log on' of either your user or any user if this is for multiple users on your computer.
Add an action, and browse your computer for the program to select the location of 'run_RGB_once.bat' that we just set up.

Now the flag will be deleted and the RGB Controller will start up upon the first logon (and only the first logon) after booting your system up.

If you are encountering issues with the scheduled tasks triggering, try unchecking all the boxes under the 'Conditions' tab when you create the task, and disabling
Fast Startup in Windows' Power Options (it is known to interfere with tasks that start upon up). Another option is disabling automatic sign-in, under
Windows, go to Settings > Accounts > Sign-in options and at the bottom there will be an option to not use your sign in information upon booting up.

Note that if this program starting up results in Windows Defender flagging the program, you can:

Adding the folder of the executable to the Windows Defender Exclusions folder, or try generating the program yourself (see make.ps1).

If ever you want this program to stop starting up on boot, just delete the two tasks that were created in Task Scheduler (or disable them).