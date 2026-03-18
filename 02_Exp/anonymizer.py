import os
import yaml
import argparse
import pydicom
import pandas as pd
from pathlib import Path

# ================= IMPORT PATH =================
def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
    
# ================= MAPPING LOGIC =================
def load_mapping(mapping_path):
    print(f"Loading mapping file: {mapping_path}")

    df = pd.read_csv(mapping_path, dtype=str)
    df.columns = df.columns.str.strip()

    mapping_dict = pd.Series(df.ID.values, index = df.NHC.values).to_dict()

    return mapping_dict

# ================= ANONYMIZATION ENGINE =================
def anonymize_dicom(dicom, new_id):
    
    # Replace Identifiers
    dicom.PatientName = new_id
    dicom.PatientID = new_id

    # Remove other patient name: # Clear value. Being a deprecated list, remove it with its DICOM codes
    tags_to_delete = [
        (0x0010, 0x1000),  # Other Patient IDs
        (0x0010, 0x1001),  # Other Patient Names
        (0x0010, 0x1002),  
        (0x0010, 0x21B0), 
        (0x0010, 0x4000), 
    ]
    for tag in tags_to_delete:
        if tag in dicom:
            del dicom[tag]

    # Remove birth date
    if 'PatientBirthDate' in dicom:
        dicom.PatientBirthDate = ""  
    if 'PatientBirthTime' in dicom:
        dicom.PatientBirthTime = ""

    # 3. Clean other standard sensitive tags 
    if 'ReferringPhysicianName' in dicom:
        dicom.ReferringPhysicianName = ""
    if 'OperatorsName' in dicom:
        dicom.OperatorsName = ""

    return dicom

def anonymize_patientFolder(treatment_folder, original_db, new_anon_id):

    rel_path = os.path.relpath(treatment_folder, original_db)
    parts = rel_path.split("\\")
    parts[0] = new_anon_id

    return os.path.join(*parts)

# ================= EXECUTION PIPELINE =================
def run_pipeline(config_yaml):

    # Parse paths
    input_root = Path(config_yaml['paths']['input_dir'])
    output_root = Path(config_yaml['paths']['output_dir'])
    mapping_path = Path(config_yaml['paths']['mapping_file'])

    # 1. Load mapping
    nhc_to_id = load_mapping(mapping_path)

    print(f"Starting scan of input directory: {input_root}")
    
    processed_count = 0

    # Walk through input directory
    for root, dirs, files in os.walk(input_root):
        print(f"Processing folder: {os.path.basename(root)}")
        
        for file in files:
            # Optional check: process only potential DICOM file: 
            # if file.lower().endswith(".dcm") or "." not in file:
            file_path = os.path.join(root, file)

            # Read DICOM file
            # Force = true cause...
            ds = pydicom.dcmread(file_path, force=True)
            
            # Extract NHC from DICOM
            # NOTE: Usually in PatientID, sometimes in PatientName. Verify on site.
            try:
                original_nhc = str(ds.PatientID).strip() 
                new_anon_id = nhc_to_id[original_nhc]
                
                # Apply anonymization rules
                anonymizedDicom = anonymize_dicom(ds, new_anon_id)
                anonymizedFileName = file.replace(original_nhc, new_anon_id)
                
                # --- SAVING LOGIC ---
                # Recreate folder structure under the NEW ID -> anon_id to be used also to anonimize the folders
                # Example Output: the same structure as the input.
                # ROOT/Patient/TreatmentX/file_X.dcm
                
                # Anonymize the patient folder
                anonymized_path = anonymize_patientFolder(root, input_root, new_anon_id)

                # Save with the same original DB structure, but with anonymized folder patient
                save_dir = os.path.join(output_root, anonymized_path)
                
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                    
                save_path = os.path.join(save_dir, anonymizedFileName)
                anonymizedDicom.save_as(save_path)
                processed_count += 1
            
            except Exception as e:
                print(f"Error in: {file_path}")
    
    print(f"\nPIPELINE FINISHED.")
    print(f"Successfully anonymized files: {processed_count}")


if __name__ == "__main__":
    print("Starting DICOM Anonymization Pipeline...")
    parser = argparse.ArgumentParser(description="DICOM Anonymization Tool")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    args = parser.parse_args()

    # Load configuration
    config_yaml = load_config(args.config)

    run_pipeline(config_yaml)