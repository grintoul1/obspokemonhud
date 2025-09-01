import json
import obspython as obs
import os.path
import requests

# Interval in seconds for the script to check the team file
check_interval = 5

# Enabled for some extra debug output to the script log
# True or False (they need to be capitals for Python)
debug = False

# The location for the JSON file
json_file = ""
json_file_contents = {}

# Boolean to toggle if to run this or not
run_boolean = False

# The style for the pokeball sprites to use
pokeball_map = {}

# Dictionary for the team pokeball image sources
team_pokeball_image_sources = []


def script_description():
    """Sets up the description

    This is a built-in OBS function.

    It outputs the value for the description part of the "Scripts" window for
    this script.
    """
    return "OBSPokemonHUD script for OBS.\nBy Tom."


def script_properties():
    """Sets up the properties section of the "Scripts" window.

    This is a built-in OBS function.

    It sets up the properties part of the "Scripts" screen for this script.

    Returns:
        properties
    """
    # Declare the properties object for us to mess with
    properties = obs.obs_properties_create()

    # Put a boolean checkbox for if this should be running or not
    obs.obs_properties_add_bool(properties, "run_boolean", "Run?")

    # Integer for how often (in seconds) this checks for changes
    obs.obs_properties_add_int(properties, "check_interval_int", "Update Interval (seconds)", 1, 120, 1)

    # Width and height pokeball
    obs.obs_properties_add_int(properties, "pokeball_height", "Ball Height (pixels)", 1, 1000, 1)
    obs.obs_properties_add_int(properties, "pokeball_width", "Ball Width (pixels)", 1, 1000, 1)

    # Add in a file path property for the team.json file
    obs.obs_properties_add_path(properties, "json_file", "Team JSON File", obs.OBS_PATH_FILE, "*.json", None)
    
    # Team image locations.
    # Set up the settings and add in a blank value as the first value

    slot1_pokeball_image_source = obs.obs_properties_add_list(
        properties,
        "slot1_pokeball_image_source",
        "Slot 1 Pokeball Source",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING
    )
    obs.obs_property_list_add_string(slot1_pokeball_image_source, "", "")

    slot2_pokeball_image_source = obs.obs_properties_add_list(
        properties,
        "slot2_pokeball_image_source",
        "Slot 2 Pokeball Source",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING
    )
    obs.obs_property_list_add_string(slot2_pokeball_image_source, "", "")

    slot3_pokeball_image_source = obs.obs_properties_add_list(
        properties,
        "slot3_pokeball_image_source",
        "Slot 3 Pokeball Source",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING
    )
    obs.obs_property_list_add_string(slot3_pokeball_image_source, "", "")

    slot4_pokeball_image_source = obs.obs_properties_add_list(
        properties,
        "slot4_pokeball_image_source",
        "Slot 4 Pokeball Source",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING
    )
    obs.obs_property_list_add_string(slot4_pokeball_image_source, "", "")

    slot5_pokeball_image_source = obs.obs_properties_add_list(
        properties,
        "slot5_pokeball_image_source",
        "Slot 5 Pokeball Source",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING
    )
    obs.obs_property_list_add_string(slot5_pokeball_image_source, "", "")

    slot6_pokeball_image_source = obs.obs_properties_add_list(
        properties,
        "slot6_pokeball_image_source",
        "Slot 6 Pokeball Source",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING
    )
    obs.obs_property_list_add_string(slot6_pokeball_image_source, "", "")

    # Iterate through each source in OBS, grabbing and adding the image ones in
    # to the list for each of the team member sources
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "image_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(slot1_pokeball_image_source, name, name)
                obs.obs_property_list_add_string(slot2_pokeball_image_source, name, name)
                obs.obs_property_list_add_string(slot3_pokeball_image_source, name, name)
                obs.obs_property_list_add_string(slot4_pokeball_image_source, name, name)
                obs.obs_property_list_add_string(slot5_pokeball_image_source, name, name)
                obs.obs_property_list_add_string(slot6_pokeball_image_source, name, name)

    # Apparently we have to release the list of sources once we are done with
    # them
    obs.source_list_release(sources)

    # If debug is enabled, print out this bit of text
    if debug:
        print("Function: Properties")

    # Finally, return the properties so they show up
    return properties


def script_defaults(settings):
    """Sets the default values

    This is a built-in OBS function.

    It sets all of the default values when the user presses the "Defaults"
    button on the "Scripts" screen.
    """

    # If debug is enabled, print out this bit of text
    if debug:
        print("Function: Defaults")

    # Set the run boolean as false by default, just in case
    obs.obs_data_set_default_bool(settings, "run_boolean", False)

    # Set the default update interval at 1 second
    obs.obs_data_set_default_int(settings, "check_interval_int", 1)
    obs.obs_data_set_default_int(settings, "pokeball_height", 100)
    obs.obs_data_set_default_int(settings, "pokeball_width", 100)


def script_update(settings):
    """Updates the settings values

    This is a built-in OBS function.

    This runs whenever a setting is changed or updated for the script. It also
    sets up and removes the timer.
    """

    # If debug is enabled, print out this bit of text
    if debug:
        print("Function: Script Update")

    # Get all of the global variables assigned in here
    global check_interval
    global json_file
    global run_boolean
    global pokeball_map
    global team_pokeball_image_sources

    # Set up the check interval
    check_interval = obs.obs_data_get_int(settings, "check_interval_int")

    pokeball_height = obs.obs_data_get_int(settings, "pokeball_height")
    pokeball_width = obs.obs_data_get_int(settings, "pokeball_width")

    # Set up the json file location
    json_file = obs.obs_data_get_string(settings, "json_file")

    # Set up the team sprites
    team_pokeball_image_sources = [
        obs.obs_data_get_string(settings, "slot1_pokeball_image_source"),
        obs.obs_data_get_string(settings, "slot2_pokeball_image_source"),
        obs.obs_data_get_string(settings, "slot3_pokeball_image_source"),
        obs.obs_data_get_string(settings, "slot4_pokeball_image_source"),
        obs.obs_data_get_string(settings, "slot5_pokeball_image_source"),
        obs.obs_data_get_string(settings, "slot6_pokeball_image_source")
    ]
    
    for source in team_pokeball_image_sources:
        setup_source(source, pokeball_height, pokeball_width)

    # Set up the run bool
    run_boolean = obs.obs_data_get_bool(settings, "run_boolean")

    # Remove the timer for the update_team function, if it exists
    obs.timer_remove(update_team)

    # If the run boolean is false, return out
    if not run_boolean:
        return

    # If the json file isn't given, return out
    if not json_file:
        return
    
    with open(f"{script_path()}map_pokeball.json", 'r') as file:
        pokeball_map = json.load(file)

    # So now, if everything is set up then set the timer
    obs.timer_add(update_team, check_interval * 1000)


def update_team():
    """Updates the different sources for the team

    This function gets run on a timer, loading up a JSON file and running the
    different update functions
    """
    # If debug is enabled, print out this bit of text
    if debug:
        print("Function: Update team")

    # Set up the required global variables
    global json_file
    global json_file_contents
    global team_pokeball_image_sources

    # Load up the JSON file in to a dictionary
    with open(json_file, 'r') as file:
        array = json.load(file)

    # If the JSON file hasn't changed since the last check, just return out
    if json_file_contents == array:
        return
    else:
        json_file_contents = array

    # Update all of the team sprites
    update_pokeball_sources(team_pokeball_image_sources[0], json_file_contents['slot1'])
    update_pokeball_sources(team_pokeball_image_sources[1], json_file_contents['slot2'])
    update_pokeball_sources(team_pokeball_image_sources[2], json_file_contents['slot3'])
    update_pokeball_sources(team_pokeball_image_sources[3], json_file_contents['slot4'])
    update_pokeball_sources(team_pokeball_image_sources[4], json_file_contents['slot5'])
    update_pokeball_sources(team_pokeball_image_sources[5], json_file_contents['slot6'])

def update_pokeball_sources(source_name, team_slot):
    # If debug is enabled, print out this bit of text
    if debug:
        print("Function: Update Pokeball sources")
    
    # If the dex number is zero or null, then give it the empty GIF file so
    # they can set sizing
    if (not team_slot["dexnumber"]) or (team_slot["dexnumber"] == 0):
        location = f"{script_path()}empty.gif"
    else:
        pokeball = get_pokeball_location(
            pokeball_map['pokeballs'],
            team_slot['pokeball'],
        )
        location = cache_image_pokeball(
            pokeball,
            pokeball_map['cache_location'],
            "pokeballs"
        )
    
    source = obs.obs_get_source_by_name(source_name)
    
    if source is not None:
        # Set the text element as being the local cached version of the file
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "file", location)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)

        # Release the source
        obs.obs_source_release(source)

def get_pokeball_location(pokeballs, pokeball):
    # If debug is enabled, print out this bit of text
    if debug:
        print("Function: Get Sprite sources")

    link = "cache/pokeballs/"

    if str(pokeball) not in pokeballs:
        print("Ball don't belong")
        return

    if pokeball in pokeballs[pokeball]:
        return link + pokeballs[pokeball]

    # If the given forms, genders, etc aren't available, just give the standard
    # sprite
    return link + pokeballs['pokeball']


def cache_image_pokeball(link, location, image_type):
    # If debug is enabled, print out this bit of text
    if debug:
        print("Function: Cache Pokeball image")

    # Set the cache folder
    cache_folder = f"{script_path()}"

    # Get the file name from the image link
    filename = f"{link}"

    return cache_folder + filename


def setup_source(source_name, height, width):
    # If debug is enabled, print out this bit of text
    if debug:
        print("Function: Setup source")

    # Get the current scene
    current_scene = obs.obs_frontend_get_current_scene()
    scene = obs.obs_scene_from_source(current_scene)
    obs.obs_source_release(current_scene)

    # Grab the source
    source = obs.obs_scene_find_source(scene, source_name)

    # This makes sure that the scaling is done right
    obs.obs_sceneitem_set_bounds_type(source, obs.OBS_BOUNDS_SCALE_INNER)

    # Set the bounding box size
    new_scale = obs.vec2()
    new_scale.x = height
    new_scale.y = width
    obs.obs_sceneitem_set_bounds(source, new_scale)
