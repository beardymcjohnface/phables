"""
Use CoverM to map to calculate coverage of unitigs.
Use combine_cov to combine the coverage values of multiple samples into one file.
"""

rule raw_coverage:
    """Map and collect the raw read counts for each sample"""
    input:
        edges = EDGES_FILE,
        r1 = os.path.join(READ_DIR,PATTERN_R1),
        r2 = os.path.join(READ_DIR,PATTERN_R2)
    output:
        tsv = temp(os.path.join(COVERM_PATH, "{sample}.counts.tsv")),
        r1 = temp(os.path.join(COVERM_PATH, "{sample}.R1.counts")),
        r2 = temp(os.path.join(COVERM_PATH, "{sample}.R2.counts")),
    threads:
        config["resources"]["jobCPU"]
    resources:
        mem_mb = config["resources"]["jobMem"]
    params:
        minimap = "-x sr --secondary=no"
    conda:
        os.path.join("..", "envs", "mapping.yaml")
    log:
        os.path.join(LOGSDIR, "{sample}.minimap.log")
    shell:
        """
        minimap2 -t {threads} {params.minimap} {input.edges} \
            <(zcat {input.r1} | tee >( wc -l > {output.r1})) \
            <(zcat {input.r2} | tee >( wc -l > {output.r2})) \
        | awk -F '\t' '{{ edges[$6]+=1; len[$6]=$7 }} END {{ for (edge in edges) {{ print edge, len[edge], edges[edge] }} }}' \
        > {output.tsv}
        """


rule rpkm_coverage:
    """convert raw coverages to RPKM values"""
    input:
        tsv = temp(os.path.join(COVERM_PATH,"{sample}.counts.tsv")),
        r1 = temp(os.path.join(COVERM_PATH,"{sample}.R1.counts")),
        r2 = temp(os.path.join(COVERM_PATH,"{sample}.R2.counts"))
    output:
        os.path.join(COVERM_PATH,"{sample}_rpkm.tsv")
    run:
        with open(input.r1, 'r') as f:
            lib = int(f.readline().strip) / 1000000
        with open(output[0], 'w') as o:
            o.write(f"Contig\t{wildcards.sample}\n")
            with open(input.tsv, 'r') as t:
                for line in t:
                    l = line.strip().split()
                    rpkm = l[1] / ( l[2] / lib )
                    o.write(f"{l[0]}\t{rpkm}\n")


rule run_combine_cov:
    input:
        files=expand(os.path.join(COVERM_PATH, "{sample}_rpkm.tsv"), sample=SAMPLES)
    output:
        os.path.join(OUTDIR, "coverage.tsv")
    params:
        covpath = COVERM_PATH,
        output = OUTDIR,
        log = os.path.join(LOGSDIR, "combine_cov.log")
    log:
        os.path.join(LOGSDIR, "combine_cov.log")
    conda: 
        os.path.join("..", "envs", "phables.yaml")
    script:
        os.path.join('..', 'scripts', 'combine_cov.py')