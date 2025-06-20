# Dependencies

Dependencies can be found in `requirements.txt`, and installed with `pip3
install -r requirements.txt`.

# Setup

__Note__: Examples for much of the setup/configuration files can be
found in the `examples` directory, along with a description of each
of the files.

## Category/Segment Names
If there are no `.pysplit` files in your base data directory (see
[General Configuration Notes](#general-configuration-notes)),
or any of its children, the "Add Run" Editor will pop up automatically,
which will allow you to create a run before starting. You will be forced
to save a run before the timer will become visible.

In the future, you can add runs from within PySplit using the `Add Run`
command in the menu, and you can edit the run that is currently open
using the `Edit Splits` command.

If you want to create splits manually, you have two options:
1. You can create the appropriate `.pysplit` file and place it somewhere
in your base data directory.
2. You can copy a `.pysplit` file and place it in your base data
directory.

## Configuring the layout

In the `defaults` directory, there is a file called `layout.json`.
This file gives the default layout for the timer. This file
provides a list of objects, where each object defines a component
to be used in the layout. Each object has the form
```
{
    "type" (required): the type of component to add
    "config" (optional): the location of the configuration file for
        this component (if desired). The referenced file has the
        location 'config/<config>.json', so set this appropriately.
}
```

Custom layouts should follow this format, and should be placed in a
directory called `layouts`.

#### Notes about layouts

1. The list of component types are given in
`Components/componentList.json`, and descriptions of each of the
types is given in that directory.

2. If a config location is not given, or if the referenced
configuration file does not exist, the configuration used for the
component is taken from `defaults/<type>.json`. This file defines
all the necessary configuration fields for the given component
type, so look at this when making a component configuration.

3. The defined components are added to the window in order from top to
bottom, so the order of component definitions does matter.

4. Custom layouts can be added to a folder called `layouts`. Before
the window is created, you will be prompted to choose a layout to
use from this directory. `system default` refers to the default layout
defined in the `defaults` directory.

## General configuration notes

As noted before, each component has the option to have custom
configuration, and the components used and their relative positions
are also customizable. However, there is also a global
configuration at `defaults/global.json`. There are only four
attributes defined in this file:

1. `baseDir`: The base directory where all the data is stored
2. `padx`: The (global) horizontal padding on the outside of the
window
3. `showMenu`: A flag which controls whether the control menu is
shown.
3. `hotkeys`: Defines the hotkeys associated with different control
actions. These are validated before being set, and a error will be
shown if an invalid hotkey is defined

## Manual Comparisons

Comparisons can be added manually using the "customComparisons" list
in a `.pysplit` file. This list is initially empty when a new run is
added, and the format of each new comparison should be the same as
the comparisons under "defaultComparisons".

Alternatively, comparisons can be edited from within PySplit using
the `Edit Splits` command in the menu.

# Included Programs

__Note__: If the three programs are not installed (see
[Installation](#installation-linux-only) for install instructions) and are just
being run as a Python script, they must be run from this directory
in order to work, as default configuration files are referenced
locally from this directory.

## runTimer.py

Usage: `python3 runTimer.py` (`pysplit` with installation)

This is a segmented timer which keeps track of segments and stores
them in a `.pysplit` file when the program is completed (either when the
final segment is completed or when the user terminates the
program).

### How it works

The program starts by prompting the user to choose a run from
a `.pysplit` file in the base data directory.
Once the user selects a run, a GUI pops up which is used for
the rest of the program. By default, there is a menu with a number
of control options, and all the options have an associated hotkey.
Below is a description of each of the options and their default hotkey.

|Function|Description|Hotkey|
|:------:|:---------:|:----:|
|`Start Run`|Starts the timer|`<Space>`|
|`Split`|Ends the current segment and starts the next one|`<Return>`|
|`Reset`|Ends the timer, regardless of whether all segments have been completed|`r`|
|`Skip Split`|Skips the current segment|`s`|
|`Change Compare`|Changes to the next comparison|`<Left>` for counter-clockwise, and `<Right>` for clockwise|
|`Pause`|Toggles whether the timer is paused|`p`|
|`Restart`|After the run has ended, resets the timer|`R`|
|`Finish`|Closes the window, prompting to save if there is unsaved data|`f`|
|`Save`|Saves any unsaved local data|`<C-s>`|
|`Choose Run`|Opens a dialog to choose the game and category|`<C-r>`|
|`Choose Layout`|Opens a dialog to choose the layout|`<C-l>`|
|`Partial Save`|Saves data about the current run which can be restored at a later time|`<C-S>`|

A couple notes about the key bindings:

1. A number of the control options are disabled at certain points
during the run. This is a list of when the control options are
enabled:

|Option|Before Start|Timer Running|Timer Paused|After End|
|:----:|:----------:|:-----------:|:----------:|:-------:|
|`Start Run`|enabled|disabled|disabled|disabled|
|`Split`|disabled|enabled|disabled|disabled|
|`Reset`|disabled|enabled|enabled|disabled|
|`Skip Split`|disabled|enabled|disabled|disabled|
|`Change Compare`|enabled|enabled|enabled|enabled|
|`Pause`|disabled|enabled|enabled|disabled|
|`Restart`|disabled|disabled|disabled|enabled|
|`Finish`|enabled|disabled|enabled|enabled|
|`Save`|enabled|enabled|enabled|enabled|
|`Choose Run`|enabled|disabled|disabled|disabled|
|`Choose Layout`|enabled|disabled|disabled|disabled|
|`Partial Save`|disabled|disabled|enabled|disabled|

2. These key bindings are configurable using the `hotkeys`
section of the configuration.

## practice.py

Usage: `python3 practice.py` (`practiceTimer` with installation)

`practice.py` allows you to practice (and improve bests for)
individual segments. This is run in the same way as `runTimer.py`,
and has mostly the same buttons and key bindings. To choose the
segment, the game and category are chosen in the same way as in
`runTimer.py`, and once the category is chosen the list of segments
is given from which one should be chosen. Hitting `Finish`
will close the window and write the results to the `.pysplit` file for
that run. Only the best time for the practiced segment will be
written - the sum of best times will be updated with the next run
of `runTimer.py`.

## variance.py

Usage: `python3 variance.py` (`timeVariance` with installation)

This simply computes the variance of all the segments to determine
which ones are most and least consistent. The variance is presented
as a percentage of the average length of the corresponding segment,
and the segments are printed in descending order by this percent
variance.

The run is chosen in the same way as in the other
two programs, and the base data directory is read (as usual) from the
user configuration.

# Installation (Linux-only)

If you are using this timer on a Linux machine, there is a simple
install script to install the program. To run it, run `./install` in
the home directory. This script does the following:

1. Installs a Python virtual environment using `requirements.txt`. The script
   prompts for a location to install it, defaulting to
   `~/.local/bin/pysplit/`.
2. Creates and installs 4 programs:
   1. `pysplit`.
   2. `practiceTimer`.
   3. `timeVariance`.
   4. `pysplitHotkeys`.
   These are the 3 programs noted above, plus an additional program that can be
   used to forward global keyboard events from Wayland to PySplit. The 3 main
   programs are set up to run using the virtual environment created in step 1.
3. Adds a user configuration file at `config/global.json` to indicate location
   of the log file, the default location for save files, and the install
   directory. Logs default to `<pysplit base>/log` and save files default to
   `<pysplit base>/splits`, where `<pysplit base>` the same directory where the
   virtual environment.
4. Installs a desktop app called `PySplit` which is linked to `pysplit`. This
   should be immediately visible when searching using the Super key, but may
   require a restart to become visible due to the app registry not always
   updating properly.
