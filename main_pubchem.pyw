
import os
try:
    import requests
except(ImportError):
    print(f'[DEBUG] Dependency "requests" not found, installing...')
    os.system("py -m pip install requests")
    import requests
try:
    import pubchempy
except(ImportError):
    print(f'[DEBUG] Dependency "pubchempy" not found, installing...')
    os.system("py -m pip install pubchempy")
    import pubchempy

try:
    from PIL import Image, ImageTk
except(ImportError):
    print(f'[DEBUG] Dependency "pillow" not found, installing...')
    os.system("py -m pip install pillow")
    from PIL import Image, ImageTk

import json
from io import BytesIO

from tkinter import Tk, messagebox
from tkinter.ttk import *

setting_template = {"makeCompoundFolder": True}
settings_filename = 'Settings.json'
#JSON DATA--------------------------
MAKE_COMPOUND_FOLDER = True
DEFAULT_COMPOUND_DIR = 'Compounds'
#-----------------------------------

"""
#loads the settings file and the api key
try:
    file = open(settings_filename, 'r')
    MAKE_COMPOUND_FOLDER = json.load(file)['makeCompoundFolder']
    file.close()
except(FileNotFoundError):
    file = open(settings_filename, 'w')
    json.dump(setting_template, file, indent=4)
    file.close()
    print(f"Settings file created.")
"""
#compound object allowes the easy retrieval from names, weight and formulas

avans_classification = {
    '1': 'H230;H231;H240;H241;H251;H252',
    '2': 'H207;H224;H242;H261;H311;H331;H336;H341;H351;H370;H371;H372;H373',
    '3': 'H206;H207;H208;H241;H250;H260;H271;H300;H310;H330;H334;H340;H350;H360;H361;H362',
    '4': 'H200;H210;H202;H203;H204;H205',
    'CMR': 'H340;H350;H360;H361;H362'
}

class compoundObj:
    def __init__(self, result):
        self.CID = result.cid
        self.name = result.iupac_name
        self.weight = result.molecular_weight
        self.formula = result.molecular_formula
        self.smiles = result.smiles
        self.Avans_class = None
        self.GHS_text = None
        try:                                                        #if already loaded it'll use the files data and save time ~1-2s...
            file = open(f'{DEFAULT_COMPOUND_DIR}/{self.name}/{self.name}.json', 'r')
            json_data = json.load(file)
            CMR = json_data["CMR"]
            Avansclass_ = json_data["GHS_class"]
            self.GHS_text = json_data['GHS_hazards']
            file.close()
            self.Avans_class = {"Class": Avansclass_, "CMR": CMR}
        except(Exception):
            self.GHS_text= self.__get_GHS_classification()
            self.GHS_stripped = self.__get_GHS_stripped()
            self.Avans_class = self.__get_avans_classification()
        
        self.image = f"https://pubchem.ncbi.nlm.nih.gov/image/imgsrv.fcgi?cid={self.CID}&t=l"
        self.propeties_template = {"Name": self.name, "Formula": self.formula, "GHS_class": self.Avans_class["Class"],"CMR": self.Avans_class["CMR"], "GHS_hazards": self.GHS_text , "Molar_mass": self.weight, "Smiles": self.smiles, "PubchemCID": self.CID, "MoleculeIMG": self.image, "credits": 'Pepin :P'}
        self.make_propeties_folder() #-> doesn't work if disabled in settings
    def search(name):
        results = pubchempy.get_compounds(name, 'name')
        return compoundObj(results[0])
    
    def __get_GHS_classification(self):
        

        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{self.CID}/JSON"
        response = requests.get(url)
        data = response.json()
        sections = data.get("Record", {}).get("Section", [])

        sub_section = []                                        #this part is a real fking bitch and really inefficient (but the fastest method FOR SOME REASON)
        for section in sections:
            if section["TOCHeading"] == "Safety and Hazards":
                sub_section.append(section)
                break
        for section in sub_section[len(sub_section)-1]['Section']:
            if section['TOCHeading'] == 'Hazards Identification':
                sub_section.append(section)
                break
        for section in sub_section[len(sub_section)-1]['Section']:
            if section['TOCHeading'] == 'GHS Classification':
                sub_section.append(section)
                break
        for section in sub_section[len(sub_section)-1]['Information']:
            if section['Name'] == 'GHS Hazard Statements':
                sub_section.append(section)
                break   
        ghs_hazards = []
        for section in sub_section[len(sub_section)-1]['Value']['StringWithMarkup']:
            ghs_hazards.append(section['String'])
        return ghs_hazards
    def __get_GHS_stripped(self):
        out = []
        hazards = self.GHS_text
        for hazard in hazards:
            out.append(hazard.split(' ')[0].strip(':'))

        index = 0
        for compound in out:
            temp = ''
            if len(compound)>4:
                for x in range(4):
                    temp+=compound[x]
                out[index] = temp
            index+=1


        return out
    
    def __get_avans_classification(self):
        highest_class = 0
        CMR = False
        for klasse in avans_classification:
            for Hsent_found in self.GHS_stripped:
                for Hsent_avans in avans_classification[klasse].split(';'):
                    if Hsent_avans == Hsent_found:
                        if klasse != "CMR":
                            highest_class = int(klasse)
                        else:
                            CMR=True
        return {'Class': highest_class, "CMR": CMR}
    
    def make_propeties_folder(self):
        if MAKE_COMPOUND_FOLDER:
            try:
                os.mkdir(DEFAULT_COMPOUND_DIR)
            except(FileExistsError):
                pass
            try:
                os.mkdir(f"{DEFAULT_COMPOUND_DIR}/{self.name}")
                file = open(f'{DEFAULT_COMPOUND_DIR}/{self.name}/{self.name}.json', 'w')
                json.dump(self.propeties_template, file, indent=4)
                file.close()
                response = requests.get(self.image)
                img = Image.open(BytesIO(response.content))
                img.save(f'{DEFAULT_COMPOUND_DIR}/{self.name}/{self.name}.png')
            except(FileExistsError):
                pass #-> dir is already made

#comp = compoundObj.search('Hexane')





gui = Tk()
title = gui.title("GHS Hazerd retriever (by Pepin:D)")

gui.geometry('1000x500')
gui.maxsize(1200, 700)
gui.minsize(1200, 700)
main_frame = None

def button_press_handle(callback=None):
    if callback:
        print("Hello!")
        callback()



def draw_mainframe():

    def get_compound(name, name_lbl, class_lbl, CMR_lbl, GHS_lbl, img_lbl):
        try:
            comp = compoundObj.search(name)
        
            img = Image.open(f"{DEFAULT_COMPOUND_DIR}/{comp.name}/{comp.name}.png")
            img = img.resize((300, 300))
            compound_name = comp.name.capitalize()
            compound_class = comp.Avans_class['Class']
            compound_CMR = comp.Avans_class['CMR']
            compound_GHS = comp.GHS_text
            line = ''
            for x in compound_GHS:
                line+=x+'\n'
            compound_GHS = line
            if compound_CMR:
                compound_CMR = "Ja"
            else:
                compound_CMR = "Nee"
            name_lbl.config(text=compound_name)
            class_lbl.config(text=compound_class)
            CMR_lbl.config(text=compound_CMR)
            GHS_lbl.config(text=compound_GHS)

            new_photo = ImageTk.PhotoImage(img)
            img_lbl.config(image=new_photo)
            img_lbl.image = new_photo

        except(IndexError):
            messagebox.showwarning(title="Not found", message=f"Compound: '{name}' not found.")



    global search_box
    main_frame = Frame(gui)
    top_frame = Frame(main_frame)
    bottom_frame = Frame(main_frame)
    result_frame = Frame(main_frame)
    GHS_FRAME = Frame(main_frame)
    img_frame= Frame(main_frame)

    main_label = Label(top_frame, text='Enter compound to retrieve GHS hazards:', font=("Arial", 20))
    main_label.grid(row=0)
    
    search_box = Entry(bottom_frame, font=("Arial", 20))
    search_box.pack(side='left', padx=0)
    
    
    name_lbl = Label(result_frame, text="", font=("Arial", 20))
    name_lbl.grid(row=2, padx=10)
    
    text_lbl = Label(result_frame, text="GHS Class:", font=("Arial", 15))
    text_lbl.grid(row=3, column=0)

    class_num_lbl = Label(result_frame, text="", font=("Arial", 15))
    class_num_lbl.grid(row=3, column=1)

    cmr_text = Label(result_frame, text="CMR:", font=("Arial", 15))
    cmr_text.grid(row=5, column=0)

    cmr_lbl = Label(result_frame, text="", font=("Arial", 15))
    cmr_lbl.grid(row=5, column=1)

    GHS_lbl = Label(GHS_FRAME, text="", font=("Arial", 9))
    GHS_lbl.grid(row=6, column=1, pady=100)

    #img = Image.open('ethanol/ethanol.png')
    #imgTK = ImageTk.PhotoImage(img)

    img_lbl = Label(img_frame)
   # img_lbl.image = imgTK
    img_lbl.grid(row=2, column=4, padx=0)

    btn = Button(bottom_frame, text="Search", command=lambda: get_compound(search_box.get(), name_lbl, class_num_lbl, cmr_lbl, GHS_lbl, img_lbl))
    btn.pack(padx=0, pady=10)

    










    top_frame.grid(row=0)
    bottom_frame.grid(row=1)
    result_frame.grid(row=2, column=0)
    GHS_FRAME.grid(row=3)
    img_frame.grid(row=2, column=4)
    
    main_frame.pack()
    

draw_mainframe()




gui.mainloop()



