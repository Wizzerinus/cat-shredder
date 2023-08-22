import glob
import subprocess

from toontown.toonbase import ConfigureUberGlobals  # noqa: F401
from toontown.toon import ClothingGlobals

all_bam_files = glob.glob("resources/**/*.bam", recursive=True)
all_strings = []
origins = {}
for file in all_bam_files:
    strings = subprocess.run(["strings", file], stdout=subprocess.PIPE).stdout.decode().split("\n")
    strings = [s.strip() for s in strings]
    strings = [s for s in strings if s[-4:].lower() in (".rgb", ".png", ".jpg") or s[-5:-1].lower() == ".jpg"]
    strings = [s.replace("resources/", "") for s in strings]
    new_strings = []
    for s in strings:
        if s[-5:-1].lower() == ".jpg":
            s = s[:-1]
        if ".." in s:
            collapse_count = s.count("../") + 1
            resolved_parent = "/".join(file.replace("resources/", "").split("/")[:-collapse_count]).strip("/")
            if resolved_parent:
                resolved_parent += "/"
            s = resolved_parent + s.replace("../", "")
        new_strings.append(s)
        if s.endswith("_a.rgb"):
            new_strings.append(s[:-6] + ".jpg")

    all_strings.extend(new_strings)
    for s in new_strings:
        if s in origins:
            origins[s] += ", " + file
        else:
            origins[s] = file

all_strings = set(all_strings)


all_images = (
    glob.glob("**/*.png", recursive=True)
    + glob.glob("**/*.rgb", recursive=True)
    + glob.glob("**/*.jpg", recursive=True)
)
all_images = [s.replace("resources/", "") for s in all_images]

exclusions = (
    []
    + ClothingGlobals.Shirts
    + ClothingGlobals.Sleeves
    + ClothingGlobals.BoyShorts
    + [x[0] for x in ClothingGlobals.Shirts]
    + ClothingGlobals.HatTextures
    + ClothingGlobals.GlassesTextures
    + ClothingGlobals.BackpackTextures
    + ClothingGlobals.ShoesTextures
    + [
        # Onscreen images
        "phase_3/maps/background.png",
        "phase_3/maps/toontown-logo.png",
        "phase_10/maps/heat.png",
        "phase_9/maps/HealthBarBosses.png",
        # These files are used in toon head code
        "phase_3/maps/eyes.png",
        "phase_3/maps/eyesClosed.png",
        "phase_3/maps/eyesSad.png",
        "phase_3/maps/eyesSadClosed.png",
        "phase_3/maps/eyesAngry.png",
        "phase_3/maps/eyesAngryClosed.png",
        "phase_3/maps/eyesSurprised.png",
        "phase_3/maps/muzzleShrtGeneric.png",
        "phase_3/maps/muzzleShortSurprised.png",
    ]
)
anti_exclusions = {
    # These files are not in any of the resource repos I used and they are in open-toontown code
    "phase_4/maps/tt_t_chr_avt_shorts_lawbotCrusher.png",
    "phase_4/maps/tt_t_chr_avt_shirt_lawbotVPIcon.png",
    "phase_4/maps/tt_t_chr_avt_shirtSleeve_lawbotCrusher.png",
    "phase_4/maps/tt_t_chr_avt_shirtSleeve_lawbotVPIcon.png",
    "phase_4/maps/tt_t_chr_avt_shirt_lawbotIcon.png",
    "phase_4/maps/tt_t_chr_avt_shirtSleeve_lawbotIcon.png",
    "phase_4/maps/tt_t_chr_avt_shirt_lawbotCrusher.png",
    # These files only are here due to a bug of how bam encoding works
    "phase_6/maps/phase_6_palette_3cmla_1.png",
    "phase_9/maps/CrossBeamx4.png",
    "phase_9/maps/phase_9_palette_3cmla_4.png",
    "phase_5/maps/phase_5_palette_1lmla_1.png",
    "phase_5/maps/phase_5_palette_4amla_1.png",
    "phase_6/maps/floor.png",
    "phase_9/maps/phase_9_palette_4amla_1.png",
    "phase_6/maps/phase_6_palette_2tmla_1.png",
}

all_images = set(all_images)
all_strings = all_strings.union(exclusions)
all_strings = {x for x in all_strings if x is not None}
all_strings = all_strings - anti_exclusions
all_strings.discard("p")

missing_textures = all_strings - all_images
if missing_textures:
    print("Detected missing textures:")
    mt_tb = []
    files = []
    for file in missing_textures:
        mt_tb.append(file)
        files.append(file)
        mt_tb.append("    " + origins.get(file, "exclusion"))
        mt_tb.append("")
    mt_text = "\n".join(mt_tb)
    files_text = "\n".join(files)
    print(mt_text)
    with open("excess.txt", "w") as f:
        f.write(files_text)
    exit(1)

excess_textures = all_images - all_strings
if excess_textures:
    print("Detected excess textures:")
    et_text = "\n".join(excess_textures)
    print(et_text)
    with open("excess.txt", "w") as f:
        f.write(et_text)
