import json
from json.decoder import JSONDecodeError
import csv
import os
import subprocess

# return cluster IDs from Salesforce report
def read_csv_file(filename):
    clusters = set()
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            if len(row) >= 2:
                cluster_id = row[1]
                if cluster_id:
                    clusters.add(cluster_id)
    return clusters

# return cluster IDs from Telesense and Superset datasets
def read_text_file(filename):
    with open(filename, 'r') as file:
        clusters = set(file.read().splitlines())
    return clusters

# write filtered cluster IDs data back to csv file
def write_csv_file(filename, rows):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Case Number", "Openshift Cluster ID", "UUID", "Account Number"])
        writer.writerows(rows)

# compare cluster IDs from Telesense, superset and Salesforce and return only the uncommon ones
def compare_clusters(csv_clusters, txt_clusters):
    missing_clusters = []
    for cluster_id in csv_clusters:
        if cluster_id not in txt_clusters:
            missing_clusters.append(cluster_id)
    return missing_clusters

# filter csv file and write missing cluster IDs to a report
def filter_csv_file(input_csv, input_txt, output_csv):
    csv_clusters = read_csv_file(input_csv)
    txt_clusters = read_text_file(input_txt)
    missing_clusters = compare_clusters(csv_clusters, txt_clusters)

    rows = []
    with open(input_csv, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)

    output_rows = [row for row in rows if len(row) >= 2 and row[1] in missing_clusters]
    write_csv_file(output_csv, output_rows)

# combine operator names from multiple text files
unique_operators = []
def combine_files(file_names):
    combined_operators = set()
    for file_name in file_names:
        with open(file_name, 'r') as file:
            operators = [line.strip() for line in file.readlines()]
            for operator in operators:
                if operator not in unique_operators:
                    combined_operators.add(operator)
                    unique_operators.append(operator)
    return combined_operators

# download must-gather attachments on the filtered ClusterIDs and generate operators report
def generateReport(csv_file, attachments_folder, combined_certified_operators, combined_redhat_operators):
    report_data = []
    with open(csv_file, "r") as file:
        reader = list(csv.reader(file, delimiter=','))

    for row in reader[1:]:
        case_number, cluster_id, attachment_id, account_number = row

        cluster_folder = os.path.join(attachments_folder, cluster_id)
        os.makedirs(cluster_folder, exist_ok=True)

        if attachment_id == "":
            break
        
        attachment_path = os.path.join(cluster_folder, attachment_id)
        subprocess.run(["/usr/bin/redhat-support-tool", "getattachment", "-c", case_number, "-u", attachment_id, "-d", cluster_folder])

        attachment_file = None
        for root, dirs, files in os.walk(cluster_folder):
            for file in files:
                if file.endswith((".tar", ".tgz", ".zip", ".rar", ".tar.gz",".tar.bz",".tar.bz2")):
                    attachment_file = os.path.join(root, file)
                    break
            if attachment_file:
                break

        if not attachment_file:
            print(f"No attachment file found for cluster ID: {cluster_id}")
            continue

        if attachment_file.endswith(".tar") or attachment_file.endswith(".tar.bz") or attachment_file.endswith(".tar.gz") or attachment_file.endswith(".tar.bz2"):
            subprocess.run(["tar", "-xf", attachment_file, "-C", cluster_folder])
        elif attachment_file.endswith(".tgz"):
            subprocess.run(["tar", "-xzf", attachment_file, "-C", cluster_folder])
        elif attachment_file.endswith(".zip"):
            subprocess.run(["unzip", "-q", attachment_file, "-d", cluster_folder])
        elif attachment_file.endswith(".rar"):
            subprocess.run(["unrar", "x", attachment_file, cluster_folder])

        image_folder = None
        for root, dirs, files in os.walk(cluster_folder):
            for directory in dirs:
                if directory.startswith("quay-io"):
                    image_folder = os.path.join(root, directory)
                    break
            if image_folder:
                break

        if not image_folder:
            print(f"Image folder not found in attachment file: {attachment_file}")
            subprocess.run(["rm", "-rf", cluster_folder])
            continue
        
        subprocess.run(["omg", "use", image_folder])
        output = subprocess.check_output(["omg", "get", "operators"]).decode()

        operators=[]
        lines = output.strip().splitlines()
        for line in lines[2:]:
            operator_name = line.split()[0]
            operators.append(operator_name)

        cluster_report = {
            "Cluster ID": cluster_id,
            "Case Number": case_number,
            "Attachment UUID": attachment_id,
            "Contact Account Number": account_number,
            "Operators Installed": operators
        }

        operators_installed = cluster_report['Operators Installed']
        certified = [op for op in operators_installed if op.split('.')[0].lower() in combined_certified_operators]
        redhat = [op for op in operators_installed if op.split('.')[0].lower() in combined_redhat_operators]
        cluster_report['Certified Operators'] = certified
        cluster_report['Red Hat Operators'] = redhat

        data = []
        try:
            with open("final-report-test.json", "r") as file:
                data = json.load(file)
        except JSONDecodeError:
            pass
        data.append(cluster_report)

        with open("final-report-test.json", "w") as output:
            json.dump(data,output, indent=4)

def main():
    certified_operators_files = ['certified-operator-4.9.txt', 'certified-operator-4.10.txt', 'certified-operator-4.11.txt', 'certified-operator-4.12.txt', 'certified-operator-4.13.txt']
    redhat_operators_files = ['redhat-operator-4.9.txt', 'redhat-operator-4.10.txt', 'redhat-operator-4.11.txt', 'redhat-operator-4.12.txt', 'redhat-operator-4.13.txt']
    combined_certified_operators = combine_files(certified_operators_files)
    combined_redhat_operators = combine_files(redhat_operators_files)

    certified_operators = set()
    for line in combined_certified_operators:
        certified_operators.add(line.strip().strip('"'))

    redhat_operators = set()
    for line in combined_redhat_operators:
        redhat_operators.add(line.strip().strip('"'))
    
    input_csv_file = 'report1686859257772.csv'
    telesense_file = 'tele.txt'
    superset_file = 'sset.txt'
    output_csv_file = 'missing_clusters.csv'

    filter_csv_file(input_csv_file, telesense_file, output_csv_file)
    filter_csv_file(output_csv_file, superset_file, output_csv_file)

    attachments_folder = "attachments"
    report_json = "final-report-test.json"
    os.makedirs(attachments_folder, exist_ok=True)
    if not os.path.isfile(report_json):
        file = open(report_json,"x")
        file.close()
    generateReport(output_csv_file, attachments_folder, certified_operators, redhat_operators)
    

if __name__ == "__main__":
    main()