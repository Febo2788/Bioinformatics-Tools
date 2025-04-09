#!/bin/bash

PHASTER_DIR="/mnt/c/Users/thora/Downloads/phaster/"
PHASTER_FILES_DIR="${PHASTER_DIR}phaster files/"
RESULTS_DIR="${PHASTER_DIR}results/"

[ ! -d "$RESULTS_DIR" ] && mkdir -p "$RESULTS_DIR"

# Path to the query ID list file
QUERY_ID_LIST_FILE="${PHASTER_DIR}phaster-queries.id"

submit_files() {
    echo "Submitting files to PHASTER..."

    for genome_file in "${PHASTER_FILES_DIR}"*; do
        if [ -f "$genome_file" ]; then
            filename=$(basename -- "$genome_file")
            
            job_id=$(curl -X POST -H "Content-Type: text/plain" --data-binary "@$genome_file" "http://phaster.ca/phaster_api" | jq -r '.job_id')

            if [ ! -z "$job_id" ]; then
                # Append the filename and job ID to the QUERY_ID_LIST_FILE
                echo "${filename}: ${job_id}" >> "$QUERY_ID_LIST_FILE"
                echo "Submitted $filename. Received Query ID: $job_id"
            else
                echo "Failed to submit $filename"
            fi
        fi
    done
}

if [ ! -f "$QUERY_ID_LIST_FILE" ]; then
    echo "Query ID list not found!"
    echo "Do you want to submit files now? [y/N]"
    read response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        submit_files
    else
        echo "No files submitted. Exiting script."
        exit 1
    fi
fi


declare -a completed_jobs
declare -a resubmit_jobs
declare -a downloaded_jobs

declare -a known_query_ids
while IFS=": " read -r filename job_id; do
    known_query_ids+=("$job_id")
done < "$QUERY_ID_LIST_FILE"

for file in "${RESULTS_DIR}"*; do
    filename=$(basename -- "$file")
    reverse_filename=$(echo "$filename" | rev)

    for (( i=1; i<=${#reverse_filename}; i++ )); do
        possible_query_id=$(echo "${reverse_filename:0:i}" | rev)
        matching_query_ids=($(printf "%s\\n" "${known_query_ids[@]}" | grep -o "$possible_query_id"))

        if [ ${#matching_query_ids[@]} -eq 1 ]; then
            query_id=$possible_query_id
            break
        fi
    done

    
    if [ ${#matching_query_ids[@]} -eq 0 ]; then
        resubmit_jobs+=("${filename}:${query_id}")
    fi

    file_prefix=$(echo "$filename" | rev | cut -c $((${#query_id} + 1))- | rev)
    downloaded_jobs+=("${file_prefix}:${query_id}")
done

while IFS=": " read -r filename job_id; do
    job_id=${job_id%% *} # Trim off any spaces and anything after them.

    status=$(curl -s "https://phaster.ca/phaster_api?acc=$job_id&type=status" | jq -r '.status')

    echo "Filename: $filename"
    echo "Query ID: $job_id"
    echo "Status: $status"
    echo "-----------------------------------"

    if [[ " ${downloaded_jobs[@]} " =~ " ${filename}:${job_id} " ]]; then
        echo "Results for $filename already downloaded."
        continue
    fi

    # If the job is complete, store it in the completed jobs list
    if [ "$status" == "Complete" ]; then
        completed_jobs+=("$filename:$job_id")
    fi

    # If the job has status 'null', store it in the resubmit jobs list
    if [ "$status" == "null" ]; then
        resubmit_jobs+=("$filename:$job_id")
    fi
done < "$QUERY_ID_LIST_FILE"

current_datetime=$(date "+%Y_%m_%d_%H_%M_%S")

echo "Do you want to save a list of all the jobs to a new file named 'job_list_${current_datetime}.txt'? [y/N]"
read save_response
if [[ "$save_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    job_list_file="${PHASTER_DIR}job_list_${current_datetime}.txt"
    for job in "${all_jobs[@]}"; do
        echo -e "$job" >> "$job_list_file"
    done
    echo "List of all jobs saved to $job_list_file"
fi

if [ ${#resubmit_jobs[@]} -gt 0 ]; then
    echo "There are ${#resubmit_jobs[@]} jobs with status 'null'."
    echo -n "Do you want to resubmit these jobs? [y/N] "
    read response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        for job in "${resubmit_jobs[@]}"; do
            IFS=":" read -r filename job_id <<< "$job"
            job_id=${job_id%% *} # Trim off any spaces and anything after them.

            # Look for the file in the 'phaster files' directory
            genome_file=$(find "$PHASTER_FILES_DIR" -type f -iname "${filename}.*" | head -n 1)

            if [ -f "$genome_file" ]; then
                # Resubmit the job and get the new job ID
                new_job_id=$(curl -X POST -H "Content-Type: text/plain" --data-binary "@$genome_file" "http://phaster.ca/phaster_api" | jq -r '.job_id')
                
                # Update the phaster-queries.id file with the new job ID and mark it as "resubmitted"
                sed -i "s/$filename: $job_id/$filename: $new_job_id (resubmitted)/" "$QUERY_ID_LIST_FILE"
                echo "Resubmitted job for $filename. New Query ID: $new_job_id"
            else
                echo "File for $filename not found in 'phaster files' directory."
            fi
        done
    fi
fi

echo "Do you want to download the completed jobs? [y/N]"
read download_response

if [[ "$download_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    # Downloading the results for the completed jobs
    for job in "${completed_jobs[@]}"; do
        IFS=":" read -r filename job_id <<< "$job"
        job_id=${job_id%% *} # Trim off any spaces and anything after them.

        output_file="${RESULTS_DIR}${filename}_${job_id}.zip"

        # If the result for this job is already downloaded, skip it
        if [[ " ${downloaded_jobs[@]} " =~ " ${filename}:${job_id} " ]]; then
            echo "Results for $filename already downloaded."
            continue
        fi

        # Query the API for the status and download link
        response=$(curl -s "https://phaster.ca/phaster_api?acc=$job_id")
        status=$(echo "$response" | jq -r '.status')

        # If the job is complete, download the ZIP
        if [ "$status" == "Complete" ]; then
            zip_url=$(echo "$response" | jq -r '.zip')
            wget "$zip_url" -O "$output_file"
            echo "Results for $filename downloaded to $output_file"
        fi
    done
fi