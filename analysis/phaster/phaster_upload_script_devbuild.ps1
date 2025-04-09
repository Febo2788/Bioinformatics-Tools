
echo "                                                   "
echo "###################################################"
echo "- Welcome to Phaster single contig genome submitter -"
echo "---------------------------------------------------"
echo "! This script submits all .fasta in local directory!"
echo "###################################################"
echo "                                                   "

$dir = "C:/Users/thora/Downloads/phaster/"

$genomes = Get-ChildItem -Path $dir -Filter *.fasta | Measure-Object | Select-Object -ExpandProperty Count
$query = Join-Path $dir "phaster-queries.id"

if (Test-Path -Path $query) {
    echo "Phaster ID list found. Please check if you already submitted your genomes to Phaster."
    exit
}
else {
    echo "                                                      "
    echo "$genomes FASTA files found in directory. Submitting."
    echo "                                                      "
}


foreach ($file in Get-ChildItem -Path $dir -Filter *.fasta) {
    $name = $file.BaseName
    echo "Submitting $file ..."
    Invoke-WebRequest -Uri "http://phaster.ca/phaster_api" -Method POST -InFile $file.FullName -OutFile "$dir\$name.out"
}

echo "                                                        "
echo "########################################################"
echo "# All genomes in directory submitted to Phaster.        #"
echo "########################################################"
echo "                                                        "

Get-Content "$dir*.out" | Select-String -Pattern 'Your job is' | ForEach-Object { $_ -replace 'Your job is', '' -replace '\s', '' } | Out-File $query

echo "########################################################"
echo "# Phaster query ID list created.                        #"
echo "#       Have a nice day!                                #"
echo "########################################################"
