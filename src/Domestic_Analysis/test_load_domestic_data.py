import pm4py
try:
# Domestic log corresponds to Domestic Declarations.xes [cite: 34]
    domestic_log = pm4py.read_xes("C:\\Users\\Carter\\OneDrive\\Documents\\KLU\\KLU Studies\\Business Process Mining\\BPMN-INT-DOM--Travel\\Data\\raw\\DomesticDeclarations.xes")

    # Print confirmation and basic case counts
    print("Domestic log loaded. Cases:", len(domestic_log))

    # Verification: check the first event of the first case to see the activity name
    print("Sample Domestic Activity:", domestic_log[0][0]['concept:name'])

except FileNotFoundError:
    print("Error: Files not found. Ensure the files are in the 'data/' directory.")
except Exception as e:
    print(f"An error occurred: {e}")