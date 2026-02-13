import os
import pydicom
import pandas as pd
from pathlib import Path

# ================= CONFIGURATION =================
# 1. Path to the folder containing RAW data (with original names/NHC)
INPUT_ROOT = r"C:\Path\To\Clinical_Raw_Data"

# 2. Path where ANONYMIZED data will be saved (ready for extraction)
OUTPUT_ROOT = r"C:\Path\To\Anonymized_Output"

# 3. Path to the mapping file downloaded from Drive (Excel or CSV)
# Ensure columns are named 'NHC' and 'ID'
MAPPING_FILE = r"C:\Path\To\patients_mapping.xlsx"

# ================= MAPPING LOGIC =================
def load_mapping(mapping_path):
    """
    Loads the mapping file (NHC -> New Anonymous ID).
    Ensures NHC column is treated as string to match DICOM tags.
    """
    print(f"🔄 Loading mapping file: {mapping_path}")
    
    if mapping_path.endswith('.csv'):
        df = pd.read_csv(mapping_path, dtype=str)
    else:
        # Requires openpyxl installed
        df = pd.read_excel(mapping_path, dtype=str)
    
    # Clean column names (remove extra spaces)
    df.columns = df.columns.str.strip()
    
    # create dictionary: { 'Original_NHC': 'New_Anonymous_ID' }
    # Example: { '289892': 'NCT07132658_1' }
    try:
        # Check if columns exist (case-sensitive)
        if 'NHC' not in df.columns or 'ID' not in df.columns:
            raise ValueError(f"Columns 'NHC' and 'ID' not found. Found: {df.columns.tolist()}")
            
        mapping_dict = pd.Series(df.ID.values, index=df.NHC.values).to_dict()
        
    except Exception as e:
        print(f"Error loading mapping: {e}")
        exit()
        
    return mapping_dict

# ================= ANONYMIZATION ENGINE =================
def anonymize_dicom(dataset, new_id):
    """
    Applies NAIARA project specific anonymization rules.
    """
    # 1. Replace Identifiers
    dataset.PatientName = new_id
    dataset.PatientID = new_id
    
    # 2. Handle Age and Birth Date
    # Requirement: Keep Age, Remove Birth Date.
    
    # Safety check: If Age is missing, try to calculate it before removing BirthDate
    if 'PatientAge' not in dataset or not dataset.PatientAge:
        if 'PatientBirthDate' in dataset and dataset.PatientBirthDate and 'StudyDate' in dataset:
            try:
                # Approximate calculation: Study Year - Birth Year
                birth_year = int(str(dataset.PatientBirthDate)[:4])
                study_year = int(str(dataset.StudyDate)[:4])
                # Format as DICOM Age string (e.g., "065Y")
                calc_age = f"{study_year - birth_year:03d}Y"
                dataset.PatientAge = calc_age
            except:
                pass # If calculation fails, proceed without age

    # REMOVE BIRTH DATE (Anonymization)
    if 'PatientBirthDate' in dataset:
        dataset.PatientBirthDate = ""  # Clear value
    if 'PatientBirthTime' in dataset:
        dataset.PatientBirthTime = ""

    # 3. Clean other standard sensitive tags (Best Practice)
    # Remove references to hospital or physicians that might indirectly identify patient
    if 'InstitutionName' in dataset:
        dataset.InstitutionName = "ANONYMIZED_SITE"
    if 'ReferringPhysicianName' in dataset:
        dataset.ReferringPhysicianName = ""
    if 'OperatorsName' in dataset:
        dataset.OperatorsName = ""
        
    return dataset

# ================= EXECUTION PIPELINE =================
def run_pipeline():
    # 1. Load mapping
    nhc_to_id = load_mapping(MAPPING_FILE)
    print(f"Found {len(nhc_to_id)} patients in mapping.")

    print(f"Starting scan of input directory: {INPUT_ROOT}")
    
    processed_count = 0
    unknown_count = 0
    error_count = 0

    # Walk through input directory
    for root, dirs, files in os.walk(INPUT_ROOT):
        for file in files:
            # Process only potential DICOM files
            if file.lower().endswith(".dcm") or "." not in file:
                file_path = os.path.join(root, file)
                
                try:
                    # Read DICOM file
                    # stop_before_pixels=False because we need to save the full file later
                    ds = pydicom.dcmread(file_path)
                    
                    # Extract NHC from DICOM
                    # NOTE: Usually in PatientID, sometimes in PatientName. Verify on site.
                    original_nhc = str(ds.PatientID).strip() 
                    
                    # Check if NHC exists in our mapping
                    if original_nhc in nhc_to_id:
                        new_anon_id = nhc_to_id[original_nhc]
                        
                        # Apply anonymization rules
                        ds = anonymize_dicom(ds, new_anon_id)
                        
                        # --- SAVING LOGIC ---
                        # Recreate folder structure under the NEW ID
                        # Example Output: OUTPUT_ROOT/NCT_ID/StudyDate/Series/.../file.dcm
                        
                        # Get relative path to keep series structure
                        rel_path = os.path.relpath(root, INPUT_ROOT)
                        
                        # Construct new path: Output -> New_ID -> Original Subfolders
                        save_dir = os.path.join(OUTPUT_ROOT, new_anon_id, rel_path)
                        
                        if not os.path.exists(save_dir):
                            os.makedirs(save_dir)
                            
                        save_path = os.path.join(save_dir, file)
                        ds.save_as(save_path)
                        processed_count += 1
                        
                    else:
                        # NHC found in DICOM but not in mapping file
                        unknown_count += 1
                        # Optional: Print only unique unknown NHCs to avoid spam
                        # print(f"⚠️ Unknown NHC: {original_nhc}")

                except Exception as e:
                    # Error reading file (not a DICOM or corrupted)
                    error_count += 1
                    # print(f"Error processing file {file}: {e}")

    print(f"\n PIPELINE FINISHED.")
    print(f"Successfully anonymized files: {processed_count}")
    print(f"Skipped files (NHC not in mapping): {unknown_count}")
    print(f"Read errors: {error_count}")

if __name__ == "__main__":
    run_pipeline()