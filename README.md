This README was google translated, and has not been updated to include new functionality in "luv" versions. [Original readme can be found here](https://github.com/trzr/Blender-CM3D2-Converter/blob/master/README.md)


# Blender-CM3D2-Converter
Model file format (.model) used in 3D adult games "[Custom Made 3D2](http://kisskiss.tv/cm3d2/)" and "[Custom Made 3D2](http://com3d2.jp/)" )
It is an add-on for handling in "[Blender](https://www.blender.org/)" which is a free 3D integrated environment.
For those who can perform basic Blender operations to some extent,
For the first time, let's start with [Blender Tutorial](https://www.google.co.jp/#q=Blender+%E3%83%81%E3%83%A5%E3%83%BC%E3%83%88%E3%83%AA%E3%82%A2%E3%83%AB) and so on.
Once you get used to it, try [CM3D2 Converter Tutorial](http://seesaawiki.jp/eastpoint/d/blender_MOD01).

**Important Note**
* Modules in this branch will not work with Blender-2.7x.
* Some functions may not work properly due to the migration work to Blender-2.8x.
* Data imported / created using Blender-CM3D2-Converter on Blender-2.7x
Even if I open it with Blender-2.8x as it is, it does not migrate normally.
  (Since texture_slots is deprecated in Blender-2.8x, it is necessary to move various data of texture_slots to node_tree before migration)
* **How to use** The following description may not be compatible with Blender-2.8x.
* Changes in Blender-2.8x
  * Changed the settings of tex, col, f that were done in the texture tab to be done from the material tab
  * Changed material property to node_tree. Along with this, the "Decorate Material" option is abolished.
  (Currently, material decoration reflects only _MainTex and _Shininess)
* Currently not supported
  * Bake function
  * Icon rendering function
  * Operation check of append_data.blend

## Table of Contents
* [Install](#Install)
* [How to Use](#How-to-Use)
* [Memo](#Memo)
* [Function list](#Function-List)
* [Terms](#Terms)
* [Model Format](#Model-Format)
* [Issues](#Issues)

## Install
First, Blender-[2.8](http://download.blender.org/release/Blender2.80/) is installed and [Japanese localization](http://ch.nicovideo.jp/hiiragik/blomaga/) It is assumed that ar501365) is done. **NOTE: "luv" version supports Blender 2.78+, 2.80+, 2.90+ and does not need Japanese localization.**
Download and unzip the file from the green "Clone or download" → "[Download ZIP](https://github.com/trzr/Blender-CM3D2-Converter/archive/bl_28.zip)" at the top right of the screen.
For Windows 10, place it so that it is "C:\Users\user_name\AppData\Roaming\Blender Foundation\Blender\2.80\scripts\addons\CM3D2 Converter\*.py".
Maybe the folder does not exist, but in that case please create it.
![Arrangement](http://i.imgur.com/QvbMDR1.jpg)
Start Blender and search for "cm3d" etc. in the add-on tab of the user settings,
If you turn on "Import-Export: CM3D2 Converter", it will be enabled temporarily.
If you want to enable it at the next startup, click the "Save Preferences" button or enable "Auto Save Preferences" and save.
![Activate](http://i.imgur.com/6jmFWxQ.jpg)
Once installed, it can be updated from the add-on setting screen or the help menu.
![Updated](http://i.imgur.com/KFvMeH0.jpg)

## How to Use
Please extract various files from the .arc file with [CM3D2 Tool](http://www.hongfire.com/forum/showthread.php/445616) etc.

.model loading
File > Import > CM3D2 Model (.model)
Exporting .model in the same way
File > Export > CM3D2 Model (.model)
![Model input / output procedure](http://i.imgur.com/p2V7D5m.jpg)

Reading .tex
UV / image editor > image > open tex file
Export .tex in the same way
UV / image editor > image > save tex file
![Tex input / output procedure](http://i.imgur.com/K7EZfz2.jpg)

.mate loading
From Properties > Materials > mate
Exporting .mate
Properties > Materials > Folder icon button
![Mate input / output procedure](http://i.imgur.com/eRMFTFZ.jpg)

All have options at the bottom left when selecting a file.

## Note

### Bone
Bone information is text data "BoneData" and "LocalBoneData",
![Text](http://i.imgur.com/pvgSZy5.jpg)
Alternatively, it is stored in an object or a custom property in the armature data.
![Custom Properties](http://i.imgur.com/HHzvdAK.jpg)
It is possible to select which one to refer to when exporting.
It is possible to change the bone settings by editing these, but it is recommended that you do not change it unless you are accustomed to it.
In addition, it seems that bone information can be easily edited by [volunteer add-on](https://github.com/trzr/Blender-CM3D2-BoneUtil).

### Object
Depending on the loaded model, the center point of the object may deviate from the center of the 3D space.
In that case, please export after aligning the center point with that position even at the time of output.

### Mesh
Even if there is a square polygon, it is automatically converted to a triangular polygon and output, but it is better to manually triangulate it.
Although it is possible to output even if it is a pentagonal polygon or more, it is highly possible that the shape will not be the expected shape, so it is recommended to manually triangulate it as well.
If there is a vertex to which no weight is assigned, an error will be issued and the process will be stopped.
Even if the total weight value is not 1.0, it will be adjusted automatically at the time of export.
Even if the number of weights is 5 or more, 4 will be automatically selected in descending order of allocation.
If the number of vertices is not less than 65535, it will be canceled.
(Because the vertices with separated UVs are counted twice, an error may occur even if it is less than 65535.)

### Material
Material information is stored according to the material, texture, and image settings.
The type of shader (CM3D2/Toony_Lighted_Outline, etc.) is
It can be changed at the top of the material tab.
![Upper material tab](http://i.imgur.com/t6fhfXt.jpg)

Also, since the material information is also stored as text (name is "Material: 0" etc.), if you change the setting at the time of output
It is also possible to refer to that. Please use the one that is easy for you to edit.

The appearance of the material may change when importing, but it does not matter when exporting.

### Texture
![Texture tab](http://i.imgur.com/4UxSChV.jpg)
Make detailed settings for the appearance of the material on the Texture tab.
There are roughly three types of setting values.
#### "Texture" type
![Texture type](http://i.imgur.com/YwwtNqQ.jpg)
Only specify the image.
There is no problem in operation even if the texture paths do not match,
For the texture name, specify the .tex file name properly.
#### "Color" type
![Color type](http://i.imgur.com/RwIFreJ.jpg)
Specify the color as the name suggests.
#### "Value" type
![Value type](http://i.imgur.com/vmMxRCW.jpg)
Set a numerical value that can also specify a decimal number.
#### Example of setting value
##### _MainTex
###### Texture that determines the color of the surface.
##### _ShadowTex
###### Texture that determines the color of the shaded area.
##### _Color
###### Additional colors. Probably multiplication, so white is invalid.
##### _ShadowColor
###### The color of the shaded area. Probably multiplication, so white is invalid.
##### _RimColor
###### The color of the reflected light that can be formed on the edge of the mesh. Invalid in black.
##### _OutlineColor
###### Outline color.
##### _Shininess
###### Gloss strength (specular in Blender).
##### _OutlineWidth
###### The thickness of the contour line.
##### _RimPower
###### The intensity and intensity of the reflected light that can be formed on the edge of the mesh.
##### _RimShift
###### The width of the reflected light that can be formed on the edge of the mesh.

### Other
There is no need to overwrite the original .model.
Even if the data name has a serial number at the end, such as "○○ .001", it will be automatically deleted.

## Extra Tools (Misc Tools)
The functions added by this add-on are unified with the icon "! [Dedicated icon](http://i.imgur.com/4RSwhad.png)".

### Create new material for CM3D2
You can create a new material with specifications that can be used with this add-on.
"Material" tab> "Create new material for CM3D2" button.
The initial value is as general as possible, but it seems that fine adjustment is required.
![Create a new material for CM3D2](http://i.imgur.com/l6TgmhY.jpg)

### Quick weight transfer
Easy to use mesh data transfer (wait transfer).
Select the model to be referred to → the model to be assigned,
"Mesh data" tab> "Vertex group" panel> "▼" button> "Quick weight transfer" button.
If you do not change the option, it will delete unnecessary vertex groups.
![Quick weight transfer](http://i.imgur.com/r7Bq6ux.jpg)

### Vertex group blur
Blur the vertex group (weight) to make it smooth.
Select a model, "Mesh Data" tab> "Vertex Group" panel>
> "▼" button> "Vertex group blur" button.
Please use when the weight copied by weight transfer is rattling.
![Vertex group blur](http://i.imgur.com/p3HNTVR.jpg)

### Shape key forced transfer
Copy the shape key from the nearest face (vertex).
Select the model to be referred to → the model to be assigned,
"Mesh data" tab> "Shape key" panel> "▼" button> "Shape key forced transfer" button.
It is possible to improve the accuracy of copying by dividing the model to be referred to in advance.
![Forced transfer of shape key](http://i.imgur.com/6y1s8Vd.jpg)

### Enlarge / reduce shape key deformation
The deformation of the shape key can be strengthened or weakened.
Select a model and select the "Mesh Data" tab> "Shape Key" panel>
> "▼" button> "Enlarge / reduce shape key deformation" button.
When the body penetrates the clothes even though the shape key has been transferred, etc.
It may be possible to correct it by increasing the deformation with this.
![Enlarge / reduce the deformation of the shape key](http://i.imgur.com/vw9NO6Z.jpg)

### Blur the shape key
Blur the deformation of the shape key to make it smooth.
Select a model and select the "Mesh Data" tab> "Shape Key" panel>
> "▼" button> "Blur shape key" button.
Please use it when the deformation copied by "Shape key forced transfer" is rattling.
![Blur the shape key](http://i.imgur.com/P69O44k.jpg)

### Convert bone / vertex group name for CM3D2 ← → Blender
The names of bones and vertex groups can be converted or restored so that they can be edited symmetrically with Blender.
Select a mesh and select the "Mesh Data" tab> "Vertex Group" panel>
> "▼" button> "Vertex group name ~" button.
Or select the armature and click the "Armature Data" tab> "Bone Name" button.
![Convert bone / vertex group name for CM3D2 ← → for Blender](http://i.imgur.com/6O5K5gm.jpg)

## Functions list
* "Properties" area-> "Armature Data" tab
--Convert bone name from CM3D2 to Blender
* Converts the bone name used in CM3D2 so that it can be edited symmetrically with Blender.
--Convert bone name from Blender to CM3D2
* Restore the bone name used in CM3D2
--Copy bone information
* Copy the bone information of the custom property to the clipboard
--Paste bone information
* Paste custom property bone information from clipboard
--Delete bone information
* Delete all bone information of custom properties
* "Properties" area-> "Modifiers" tab
--Forced application of modifiers
* Forced to apply even to mesh modifiers with shape keys
* "Properties" area-> "Mesh Data" tab-> "Vertex Group" panel
--Convert vertex group name from CM3D2 to Blender
* Converts the bone name (vertex group name) used in CM3D2 so that it can be edited symmetrically with Blender.
--Convert vertex group name from Blender to CM3D2
* Revert to the bone name (vertex group name) used in CM3D2
* "UV / Image Editor" area → Header
* "UV / Image Editor" area-> Properties-> "Image" panel
* Upper right of the screen ("Information" area → Header)
--Check the number of vertices
* Check if the selected mesh fits within the number of vertices that can be output by Converter
* "3D View" area → Add (Shift + A) → CM3D2
--Import the body for CM3D2
* Import CM3D2 related elements into the current scene
* "3D view" area → Add (Shift + A) → Curve
--Add a tuft of hair
* Add an animated hair tuft
* Top of screen ("Information" area → Header) → Help
--Updated CM3D2 Converter
* Download the latest version of CM3D2 Converter add-on from GitHub and overwrite it
--Open the CM3D2 Converter setting screen
* Display the setting screen of CM3D2 Converter add-on
* "Properties" area-> "Material" tab
--Create a new material for CM3D2
* Blender-CM3D2-Create a new material that can be used with Converter
--Paste material from clipboard
* Create a new material from the material information in the clipboard
--Paste material from clipboard
* Overwrite material information from text in clipboard
--Copy material to clipboard
* Copy the displayed material to the clipboard in text format
--Decorate material
* Decorate all the materials in the slot according to the settings
--See this texture
* See this texture
* "Properties" area-> "Mesh data" tab-> "Shape key" panel-> ▼ button
--Quick shape key transfer
* Fast transfer the shape keys of other selected meshes to the active mesh
--Spatial blur / shape key transfer
* Transfers the shape keys of other selected meshes to the active mesh by blurring them farther.
--Multiply the shape key transformation
* Multiply the shape key deformation by a number to increase or decrease the strength of the deformation
--Shape key blur
* Blur active or all shape keys
--Based on this shape key
* Base the active shape key on other shape keys
* "Properties" area-> "Mesh data" tab-> "Vertex group" panel-> ▼ button
--Quick wait transfer
* Fast transfer vertex groups of other selected meshes to the active mesh
--Spatial blur / weight transfer
* Transfers the vertex groups of other selected meshes to the active mesh by blurring them farther.
--Vertex group blur
* Blur active or all vertex groups
--Old / vertex group blur
* Blur active or all vertex groups
--Multiply the vertex group
* Multiply the weights of the vertex group by a number to increase or decrease the strength of the weights.
--Delete unassigned vertex group
* Delete all vertex groups that are not assigned to any vertex
* Properties area → Objects tab
--Copy bone information
* Copy the bone information of the custom property to the clipboard
--Paste bone information
* Paste custom property bone information from clipboard
--Delete bone information
* Delete all bone information of custom properties
* Properties area → Objects tab → Transforms panel
--Align objects
* Align the center position of the active object with the center position of other selected objects
* Properties area → Render tab → Bake panel
--Create an image for baking
* Quickly prepare an empty image for baking on the active object
--AO Bake
* Quickly bake AO to active object
--Pseudo AO / Bake
* Quickly bake pseudo AO to active object
--Hemilite Bake
* Quickly bake the shade of hemilite on the active object
--Shadow / Bake
* Quickly bake shadows on active objects
--Side shade / bake
* Quickly bake side shades on active objects
--Gradient bake
* Quickly bake gradients to active objects
--Metal / Bake
* Quickly bake to active objects in a metallic style
--Hair Bake
* Quickly bake CM3D2 hair-like textures on active objects
--UV edge / bake
* Quickly bake UV edges black on active objects
--Mesh edge / bake
* Quickly bake the edges of the mesh black to the active object
--Density / Bake
* Quickly bake density to active objects
--Distance between meshes / bake
* Bake the distance between the active object and other objects
--Bulge / Bake
* Bake the bulging part of the active object white
--White liquid bake
* Bake a white liquid on the active object
* "Properties" area-> "Render" tab-> "Render" panel
--Rendering icons for CM3D2 menu
* Renders an image that could be used for the icon image in CM3D2
* "Properties" area → "Texture" tab
--Display image
* Display the specified image in the UV / image editor
-Find textures
* Find and open the tex file in the installation folder of the CM3D2 main unit.
--Sync settings to preview
* Apply settings to texture preview for clarity
--Select Toon
* You can select the toon texture that is included in CM3D2 by default
--Automatically set color settings
* Automatically set color-related settings from the texture color information
--Save as tex
* Save the texture image as tex in the same folder
--Set color setting value
* Set the color type setting
* "Text Editor" area → Header
--Display text
* Display the specified text in this area
--Copy text bone information
* Paste the text bone information into a custom property and copy it to the clipboard
--Paste text bone information
* Paste the bone information in the clipboard into the text data
--Delete all material information text
* Remove all material text available in CM3D2
* "3D view" area → mesh edit mode → "W" key
--The drawing order of the selected surface is in the foreground
* Sorts the drawing order of the selected faces to the front / back.
* "3D View" area → Pause mode → Ctrl + A (Pause → Apply)
--Body in the current pose
* Create a body that makes it easier to model costumes in the current pose
* "3D View" area → "Weight Paint" mode → Tool shelf → "Weight Tools" panel
--Blur the vertex group of the selection
* Blur the vertex group assignments for the selected mesh
--Four arithmetic operations on the vertex group of the selection
* Performs four arithmetic operations on the allocation of vertex groups in the selected mesh.

## Terms
Please adhere to the [Official MOD Terms](http://kisskiss.tv/kiss/diary.php?no=558).

## Model Format
* (String) Fixed to "CM3D2_MESH"
* (Int) Version number
* (String) Model name
* (String) Base bone name
* (Int) Number of bones
* for number of bones
-(String) Bone name
-(Char) Flag?
* for number of bones
-(Int) Parent number
* for number of bones
-(Float × 3) Bone position
-(Float x 4) Bone rotation
* (Int) Number of vertices
* (Int) Number of meshes (number of materials)
* (Int) Number of bones used
* for Number of bones used
-(String) Bone name
* for Number of bones used
-(Float × 16) Bone transformation matrix
* for number of vertices
-(Float × 3) Vertex position
-(Float × 3) Normal direction
-(Float x 2) UV position
* (Int) Number of vertices (0 if tangent space information is not output)
* for number of vertices
-(Float × 4) Tangent (x, y, z) binormal
* for number of vertices
-(Short x 4) Assign bone number x 4
-(Float x 4) Assigned weight x 4
* for mesh number
-(Int) Number of pages
--for number of pages
* (Short) Vertex number
* (Int) Number of materials (number of meshes)
* for number of materials
-(String) Material name
-(String) Shader used
-(String) Shader used
--while
* (String) Setting value type
* if setting value type == "tex"
-(String) Texture name
-(String) Texture Type
--if texture type == "tex2d"
* (String) Image name
* (String) Image path
* (Float x 4) Color (RGBA)
* else if setting value type == "col"
-(String) Color name
-(Float x 4) Color (RGBA)
* else if setting value type == "f"
-(String) Value name
-(Float) value
* else if setting value type == "end"
--break
* while
-(String) Setting value type
--if setting value type == "morph"
* (String) Morph name
* (Int) Number of changed vertices
* for Number of changed vertices
-(Short) Vertex number
-(Float × 3) Vertex position
-(Float × 3) Normal direction
--other if setting value type == "end"
* break

## Task
* Make bone information editable by human power ([Realized by volunteer add-on](https://github.com/trzr/Blender-CM3D2-BoneUtil))
* Full support for motion files (.anm)
