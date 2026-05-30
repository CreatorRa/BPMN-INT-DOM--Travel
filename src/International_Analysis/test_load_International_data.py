import pm4py

# Load raw event logs using the modern unified API
# Paths should point to where you stored the .xes files provided for the assignment
try:
    # International log corresponds to International Declarations.xes [cite: 33]
    international_log = pm4py.read_xes("C:\\Users\\user\\OneDrive\\Desktop\\KUHNE LOGISTIC UNIVERSITY\\SEMESTER 2\\BPM\\BPMN-INT-DOM--Travel\\Data\\raw\\InternationalDeclarations.xes")

    # Print confirmation and basic case counts
    print("International log loaded. Cases:", len(international_log))
   

    # Verification: check the first event of the first case to see the activity name
    print("\nSample International Activity:", international_log[0][0]['concept:name'])
  

except FileNotFoundError:
    print("Error: Files not found. Ensure the files are in the 'data/' directory.")
except Exception as e:
    print(f"An error occurred: {e}")

