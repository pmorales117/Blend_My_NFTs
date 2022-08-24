# Purpose:
# This file takes a given Batch created by dna_generator.py and tells blender to render the image or export a 3D model
# to the NFT_Output folder.

import bpy
import os
import ssl
import time
import json
import smtplib
import datetime
import platform

from .helpers import TextColors, Loader
from .metadata_templates import createCardanoMetadata, createSolanaMetaData, createErc721MetaData


# Save info
def save_batch(batch, file_name):
    saved_batch = json.dumps(batch, indent=1, ensure_ascii=True)

    with open(os.path.join(file_name), 'w') as outfile:
        outfile.write(saved_batch + '\n')


def save_generation_state(input):
    """
    Saves date and time of generation start, and generation types; Images, Animations, 3D Models, and the file types for
    each.
    """
    file_name = os.path.join(input.batch_json_save_path, "Batch{}.json".format(input.batchToGenerate))
    batch = json.load(open(file_name))

    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    current_date = datetime.datetime.now().strftime("%d/%m/%Y")
    local_timezone = str(datetime.datetime.now(datetime.timezone.utc))

    if "Generation Save" in batch:
        batch_save_number = int(batch[f"Generation Save"].index(batch[f"Generation Save"][-1]))
    else:
        batch_save_number = 0

    batch["Generation Save"] = list()
    batch["Generation Save"].append({
            "Batch Save Number": batch_save_number + 1,
            "DNA Generated": None,
            "Generation Start Date and Time": [current_time, current_date, local_timezone],
            "Render_Settings": {
                    "nftName": input.nftName,
                    "save_path": input.save_path,
                    "nftsPerBatch": input.nftsPerBatch,
                    "batch_to_generate": input.batchToGenerate,
                    "collectionSize": input.collectionSize,

                    "Blend_My_NFTs_Output": input.Blend_My_NFTs_Output,
                    "batch_json_save_path": input.batch_json_save_path,
                    "nftBatch_save_path": input.nftBatch_save_path,

                    "enableImages": input.enableImages,
                    "imageFileFormat": input.imageFileFormat,

                    "enableAnimations": input.enableAnimations,
                    "animationFileFormat": input.animationFileFormat,

                    "enableModelsBlender": input.enableModelsBlender,
                    "modelFileFormat": input.modelFileFormat,

                    "enableCustomFields": input.enableCustomFields,

                    "cardanoMetaDataBool": input.cardanoMetaDataBool,
                    "solanaMetaDataBool": input.solanaMetaDataBool,
                    "erc721MetaData": input.erc721MetaData,

                    "cardano_description": input.cardano_description,
                    "solana_description": input.solana_description,
                    "erc721_description": input.erc721_description,

                    "enableMaterials": input.enableMaterials,
                    "materialsFile": input.materialsFile,

                    "enableLogic": input.enableLogic,
                    "enable_Logic_Json": input.enable_Logic_Json,
                    "logicFile": input.logicFile,

                    "enableRarity": input.enableRarity,

                    "enableAutoShutdown": input.enableAutoShutdown,

                    "specify_timeBool": input.specify_timeBool,
                    "hours": input.hours,
                    "minutes": input.minutes,

                    "emailNotificationBool": input.emailNotificationBool,
                    "sender_from": input.sender_from,
                    "email_password": input.email_password,
                    "receiver_to": input.receiver_to,

                    "custom_Fields": input.custom_Fields,
            },
    })

    save_batch(batch, file_name)


def save_completed(full_single_dna, a, x, batch_json_save_path, batch_to_generate):
    """Saves progress of rendering to batch.json file."""

    file_name = os.path.join(batch_json_save_path, "Batch{}.json".format(batch_to_generate))
    batch = json.load(open(file_name))
    index = batch["BatchDNAList"].index(a)
    batch["BatchDNAList"][index][full_single_dna]["Complete"] = True
    batch["Generation Save"][-1]["DNA Generated"] = x

    save_batch(batch, file_name)


# Exporter functions:
def get_batch_data(batch_to_generate, batch_json_save_path):
    """
    Retrieves a given batches data determined by renderBatch in config.py
    """

    file_name = os.path.join(batch_json_save_path, "Batch{}.json".format(batch_to_generate))
    batch = json.load(open(file_name))

    nfts_in_batch = batch["nfts_in_batch"]
    hierarchy = batch["hierarchy"]
    batch_dna_list = batch["batch_dna_list"]

    return nfts_in_batch, hierarchy, batch_dna_list


def render_and_save_nfts(input):
    """
    Renders the NFT DNA in a Batch#.json, where # is renderBatch in config.py. Turns off the viewport camera and
    the render camera for all items in hierarchy.
    """

    time_start_1 = time.time()

    # If failed Batch is detected and user is resuming its generation:
    if input.fail_state:
        print(f"{TextColors.ERROR}\nResuming Batch #{input.failed_batch}\n{TextColors.RESET}")
        nfts_in_batch, hierarchy, batch_dna_list = get_batch_data(input.failed_batch, input.batch_json_save_path)
        for a in range(input.failed_dna):
            del batch_dna_list[0]
        x = input.failed_dna + 1

    # If user is generating the normal way:
    else:
        print(f"\nGenerating Batch #{input.batchToGenerate}\n")
        nfts_in_batch, hierarchy, batch_dna_list = get_batch_data(input.batchToGenerate, input.batch_json_save_path)
        save_generation_state(input)
        x = 1

    if input.enableMaterials:
        materials_file = json.load(open(input.materialsFile))

    for a in batch_dna_list:
        full_single_dna = list(a.keys())[0]
        order_num = a[full_single_dna]['order_num']

        # Material handling:
        if input.enableMaterials:
            single_dna, material_dna = full_single_dna.split(':')

        if not input.enableMaterials:
            single_dna = full_single_dna

        def match_dna_to_variant(single_dna):
            """
            Matches each DNA number separated by "-" to its attribute, then its variant.
            """

            list_attributes = list(hierarchy.keys())
            list_dna_deconstructed = single_dna.split('-')
            dna_dictionary = {}

            for i, j in zip(list_attributes, list_dna_deconstructed):
                dna_dictionary[i] = j

            for x in dna_dictionary:
                for k in hierarchy[x]:
                    k_num = hierarchy[x][k]["number"]
                    if k_num == dna_dictionary[x]:
                        dna_dictionary.update({x: k})
            return dna_dictionary

        def match_material_dna_to_material(single_dna, material_dna, materials_file):
            """
            Matches the Material DNA to it's selected Materials unless a 0 is present meaning no material for that variant was selected.
            """
            list_attributes = list(hierarchy.keys())
            list_dna_deconstructed = single_dna.split('-')
            list_material_dna_deconstructed = material_dna.split('-')

            full_dna_dict = {}

            for attribute, variant, material in zip(
                    list_attributes,
                    list_dna_deconstructed,
                    list_material_dna_deconstructed
            ):

                for var in hierarchy[attribute]:
                    if hierarchy[attribute][var]['number'] == variant:
                        variant = var

                if material != '0':  # If material is not empty
                    for variant_m in materials_file:
                        if variant == variant_m:
                            # Getting Materials name from Materials index in the Materials List
                            materials_list = list(materials_file[variant_m]["Material List"].keys())

                            material = materials_list[int(material) - 1]  # Subtract 1 because '0' means empty mat
                            break

                full_dna_dict[variant] = material

            return full_dna_dict

        metadata_material_dict = {}

        if input.enableMaterials:
            material_dna_dictionary = match_material_dna_to_material(single_dna, material_dna, materials_file)

            for var_mat in list(material_dna_dictionary.keys()):
                if material_dna_dictionary[var_mat]!='0':
                    if not materials_file[var_mat]['Variant Objects']:
                        """
                        If objects to apply material to not specified, apply to all objects in Variant collection.
                        """
                        metadata_material_dict[var_mat] = material_dna_dictionary[var_mat]

                        for obj in bpy.data.collections[var_mat].all_objects:
                            selected_object = bpy.data.objects.get(obj.name)
                            selected_object.active_material = bpy.data.materials[material_dna_dictionary[var_mat]]

                    if materials_file[var_mat]['Variant Objects']:
                        """
                        If objects to apply material to are specified, apply material only to objects specified withing 
                        the Variant collection.
                        """
                        metadata_material_dict[var_mat] = material_dna_dictionary[var_mat]

                        for obj in materials_file[var_mat]['Variant Objects']:
                            selected_object = bpy.data.objects.get(obj)
                            selected_object.active_material = bpy.data.materials[material_dna_dictionary[var_mat]]

        # Turn off render camera and viewport camera for all collections in hierarchy
        for i in hierarchy:
            for j in hierarchy[i]:
                try:
                    bpy.data.collections[j].hide_render = True
                    bpy.data.collections[j].hide_viewport = True
                except KeyError:
                    raise TypeError(
                            f"\n{TextColors.ERROR}Blend_My_NFTs Error:\n"
                            f"The Collection '{j}' appears to be missing or has been renamed. If you made any changes to "
                            f"your .blend file scene, ensure you re-create your NFT Data so Blend_My_NFTs can read your "
                            f"scene. For more information see:{TextColors.RESET}"
                            f"\nhttps://github.com/torrinworx/Blend_My_NFTs#blender-file-organization-and-structure\n"
                    )

        dna_dictionary = match_dna_to_variant(single_dna)
        name = input.nftName + "_" + str(order_num)

        # Change Text Object in Scene to match DNA string:
        # Variables that can be used: full_single_dna, name, order_num
        # ob = bpy.data.objects['Text']  # Object name
        # ob.data.body = str(f"DNA: {full_single_dna}")  # Set text of Text Object ob

        print(f"\n{TextColors.OK}======== Generating NFT {x}/{nfts_in_batch}: {name} ========{TextColors.RESET}")
        print(f"\nVariants selected:")
        print(f"{dna_dictionary}")
        if input.enableMaterials:
            print(f"\nMaterials selected:")
            print(f"{material_dna_dictionary}")

        print(f"\nDNA Code:{full_single_dna}")

        for c in dna_dictionary:
            collection = dna_dictionary[c]
            if collection != '0':
                bpy.data.collections[collection].hide_render = False
                bpy.data.collections[collection].hide_viewport = False

        time_start_2 = time.time()

        # Main paths for batch sub-folders:
        batch_folder = os.path.join(input.nftBatch_save_path, "Batch" + str(input.batchToGenerate))

        image_folder = os.path.join(batch_folder, "Images")
        animation_folder = os.path.join(batch_folder, "Animations")
        model_folder = os.path.join(batch_folder, "Models")
        bmnft_data_folder = os.path.join(batch_folder, "BMNFT_data")

        image_path = os.path.join(image_folder, name)
        animation_path = os.path.join(animation_folder, name)
        model_path = os.path.join(model_folder, name)

        cardano_metadata_path = os.path.join(batch_folder, "Cardano_metadata")
        solana_metadata_path = os.path.join(batch_folder, "Solana_metadata")
        erc721_metadata_path = os.path.join(batch_folder, "Erc721_metadata")

        def check_failed_exists(file_path):
            """
            Delete a file if a fail state is detected and if the file being re-generated already exists. Prevents
            animations from corrupting.
            """
            if input.fail_state:
                if os.path.exists(file_path):
                    os.remove(file_path)

        # Generation/Rendering:
        if input.enableImages:

            print(f"{TextColors.OK}-------- Image --------{TextColors.RESET}")

            image_render_time_start = time.time()

            check_failed_exists(image_path)

            def render_image():
                if not os.path.exists(image_folder):
                    os.makedirs(image_folder)

                bpy.context.scene.render.filepath = image_path
                bpy.context.scene.render.image_settings.file_format = input.imageFileFormat
                bpy.ops.render.render(write_still=True)

            # Loading Animation:
            loading = Loader(f'Rendering Image {x}/{nfts_in_batch}...', '').start()
            render_image()
            loading.stop()

            image_render_time_end = time.time()

            print(
                    f"{TextColors.OK}Rendered image in {image_render_time_end - image_render_time_start}s."
                    f"\n{TextColors.RESET}"
            )

        if input.enableAnimations:
            print(f"{TextColors.OK}-------- Animation --------{TextColors.RESET}")

            animation_render_time_start = time.time()

            check_failed_exists(animation_path)

            def render_animation():
                if not os.path.exists(animation_folder):
                    os.makedirs(animation_folder)

                if input.animationFileFormat == "MP4":
                    bpy.context.scene.render.filepath = animation_path
                    bpy.context.scene.render.image_settings.file_format = "FFMPEG"

                    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
                    bpy.context.scene.render.ffmpeg.codec = 'H264'
                    bpy.ops.render.render(animation=True)

                elif input.animationFileFormat == 'PNG':
                    if not os.path.exists(animation_path):
                        os.makedirs(animation_path)

                    bpy.context.scene.render.filepath = os.path.join(animation_path, name)
                    bpy.context.scene.render.image_settings.file_format = input.animationFileFormat
                    bpy.ops.render.render(animation=True)

                elif input.animationFileFormat == 'TIFF':
                    if not os.path.exists(animation_path):
                        os.makedirs(animation_path)

                    bpy.context.scene.render.filepath = os.path.join(animation_path, name)
                    bpy.context.scene.render.image_settings.file_format = input.animationFileFormat
                    bpy.ops.render.render(animation=True)

                else:
                    bpy.context.scene.render.filepath = animation_path
                    bpy.context.scene.render.image_settings.file_format = input.animationFileFormat
                    bpy.ops.render.render(animation=True)

            # Loading Animation:
            loading = Loader(f'Rendering Animation {x}/{nfts_in_batch}...', '').start()
            render_animation()
            loading.stop()

            animation_render_time_end = time.time()

            print(
                    f"{TextColors.OK}Rendered animation in {animation_render_time_end - animation_render_time_start}s."
                    f"\n{TextColors.RESET}"
            )

        if input.enableModelsBlender:
            print(f"{TextColors.OK}-------- 3D Model --------{TextColors.RESET}")

            model_generation_time_start = time.time()

            def generate_models():
                if not os.path.exists(model_folder):
                    os.makedirs(model_folder)

                for i in dna_dictionary:
                    coll = dna_dictionary[i]
                    if coll != '0':
                        for obj in bpy.data.collections[coll].all_objects:
                            obj.select_set(True)

                for obj in bpy.data.collections['Script_Ignore'].all_objects:
                    obj.select_set(True)

                # Remove objects from 3D model export:
                # remove_objects: list = [
                # ]
                #
                # for obj in bpy.data.objects:
                #     if obj.name in remove_objects:
                #         obj.select_set(False)

                if input.modelFileFormat == 'GLB':
                    check_failed_exists(f"{model_path}.glb")
                    bpy.ops.export_scene.gltf(
                            filepath=f"{model_path}.glb",
                            check_existing=True,
                            export_format='GLB',
                            export_keep_originals=True,
                            use_selection=True
                    )
                if input.modelFileFormat == 'GLTF_SEPARATE':
                    check_failed_exists(f"{model_path}.gltf")
                    check_failed_exists(f"{model_path}.bin")
                    bpy.ops.export_scene.gltf(
                            filepath=f"{model_path}",
                            check_existing=True,
                            export_format='GLTF_SEPARATE',
                            export_keep_originals=True,
                            use_selection=True
                    )
                if input.modelFileFormat == 'GLTF_EMBEDDED':
                    check_failed_exists(f"{model_path}.gltf")
                    bpy.ops.export_scene.gltf(
                            filepath=f"{model_path}.gltf",
                            check_existing=True,
                            export_format='GLTF_EMBEDDED',
                            export_keep_originals=True,
                            use_selection=True
                    )
                elif input.modelFileFormat == 'FBX':
                    check_failed_exists(f"{model_path}.fbx")
                    bpy.ops.export_scene.fbx(
                            filepath=f"{model_path}.fbx",
                            check_existing=True,
                            use_selection=True
                    )
                elif input.modelFileFormat == 'OBJ':
                    check_failed_exists(f"{model_path}.obj")
                    bpy.ops.export_scene.obj(
                            filepath=f"{model_path}.obj",
                            check_existing=True,
                            use_selection=True,
                    )
                elif input.modelFileFormat == 'X3D':
                    check_failed_exists(f"{model_path}.x3d")
                    bpy.ops.export_scene.x3d(
                            filepath=f"{model_path}.x3d",
                            check_existing=True,
                            use_selection=True
                    )
                elif input.modelFileFormat == 'STL':
                    check_failed_exists(f"{model_path}.stl")
                    bpy.ops.export_mesh.stl(
                            filepath=f"{model_path}.stl",
                            check_existing=True,
                            use_selection=True
                    )
                elif input.modelFileFormat == 'VOX':
                    check_failed_exists(f"{model_path}.vox")
                    bpy.ops.export_vox.some_data(filepath=f"{model_path}.vox")

            # Loading Animation:
            loading = Loader(f'Generating 3D model {x}/{nfts_in_batch}...', '').start()
            generate_models()
            loading.stop()

            model_generation_time_end = time.time()

            print(
                    f"{TextColors.OK}Generated 3D model in {model_generation_time_end - model_generation_time_start}s."
                    f"\n{TextColors.RESET}"
            )

        # Generating Metadata:
        if input.cardanoMetaDataBool:
            if not os.path.exists(cardano_metadata_path):
                os.makedirs(cardano_metadata_path)
            createCardanoMetadata(
                    name,
                    order_num,
                    full_single_dna,
                    dna_dictionary,
                    metadata_material_dict,
                    input.custom_Fields,
                    input.enableCustomFields,
                    input.cardano_description,
                    cardano_metadata_path
            )

        if input.solanaMetaDataBool:
            if not os.path.exists(solana_metadata_path):
                os.makedirs(solana_metadata_path)
            createSolanaMetaData(
                    name,
                    order_num,
                    full_single_dna,
                    dna_dictionary,
                    metadata_material_dict,
                    input.custom_Fields,
                    input.enableCustomFields,
                    input.solana_description,
                    solana_metadata_path
            )

        if input.erc721MetaData:
            if not os.path.exists(erc721_metadata_path):
                os.makedirs(erc721_metadata_path)
            createErc721MetaData(
                    name,
                    order_num,
                    full_single_dna,
                    dna_dictionary,
                    metadata_material_dict,
                    input.custom_Fields,
                    input.enableCustomFields,
                    input.erc721_description,
                    erc721_metadata_path
            )

        if not os.path.exists(bmnft_data_folder):
            os.makedirs(bmnft_data_folder)

        for b in dna_dictionary:
            if dna_dictionary[b] == "0":
                dna_dictionary[b] = "Empty"

        meta_data_dict = {
                "name": name,
                "nft_dna": a,
                "nft_variants": dna_dictionary,
                "material_attributes": metadata_material_dict
        }

        json_meta_data = json.dumps(meta_data_dict, indent=1, ensure_ascii=True)

        with open(os.path.join(bmnft_data_folder, "Data_" + name + ".json"), 'w') as outfile:
            outfile.write(json_meta_data + '\n')

        print(f"Completed {name} render in {time.time() - time_start_2}s")

        save_completed(full_single_dna, a, x, input.batch_json_save_path, input.batchToGenerate)

        x += 1

    for i in hierarchy:
        for j in hierarchy[i]:
            bpy.data.collections[j].hide_render = False
            bpy.data.collections[j].hide_viewport = False

    batch_complete_time = time.time() - time_start_1

    print(f"\nAll NFTs successfully generated and sent to {input.nftBatch_save_path}"
          f"\nCompleted all renders in Batch{input.batchToGenerate}.json in {batch_complete_time}s\n")

    batch_info = {"Batch Render Time": batch_complete_time, "Number of NFTs generated in Batch": x - 1,
                  "Average time per generation": batch_complete_time / x - 1}

    batch_info_folder = os.path.join(input.nftBatch_save_path, "Batch" + str(input.batchToGenerate), "batch_info.json")
    save_batch(batch_info, batch_info_folder)

    # Send Email that Batch is complete:
    if input.emailNotificationBool:
        port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        sender_email = input.sender_from  # Enter your address
        receiver_email = input.receiver_to  # Enter receiver address
        password = input.email_password

        # Get batch info for message:
        if input.fail_state:
            batch = input.fail_state
            batch_data = get_batch_data(input.failed_batch, input.batch_json_save_path)

        else:
            batch_data = get_batch_data(input.batchToGenerate, input.batch_json_save_path)

            batch = input.batchToGenerate

        generation_time = str(datetime.timedelta(seconds=batch_complete_time))

        message = f"""\
        Subject: Batch {batch} completed {x - 1} NFTs in {generation_time} (h:m:s)

        Generation Time:
        {generation_time.split(':')[0]} Hours, 
        {generation_time.split(':')[1]} Minutes, 
        {generation_time.split(':')[2]} Seconds
        Batch Data:

            {batch_data}

        This message was sent from an instance of the Blend_My_NFTs Blender add-on.
        """

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

    # Automatic Shutdown:
    # If user selects automatic shutdown but did not specify time after Batch completion
    def shutdown(time):
        plateform = platform.system()

        if plateform == "Windows":
            os.system(f"shutdown /s /t {time}")
        if plateform == "Darwin":
            os.system(f"shutdown /s /t {time}")

    if input.enableAutoShutdown and not input.specify_timeBool:
        shutdown(0)

    # If user selects automatic shutdown and specify time after Batch completion
    if input.enableAutoShutdown and input.specify_timeBool:
        hours = (int(input.hours) / 60) / 60
        minutes = int(input.minutes) / 60
        total_sleep_time = hours + minutes

        # time.sleep(total_sleep_time)

        shutdown(total_sleep_time)
