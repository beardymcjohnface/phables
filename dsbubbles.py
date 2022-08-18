#!/usr/bin/env python3

import logging
import subprocess
import sys
import time

import click
import networkx as nx
from igraph import *
from tqdm import tqdm

from dsbubbles_utils import component_utils, edge_graph_utils, edge_utils, gene_utils
from dsbubbles_utils.genome_utils import GenomeComponent, GenomePath

__author__ = "Vijini Mallawaarachchi"
__copyright__ = "Copyright 2022, ds-bubbles Project"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Vijini Mallawaarachchi"
__email__ = "vijini.mallawaarachchi@flinders.edu.au"
__status__ = "Development"

MAX_VAL = sys.maxsize
FASTA_LINE_LEN = 60

# Sample command
# -------------------------------------------------------------------
# python dsbubbles.py  -g /path/to/assembly_graph.gfa
#                      -c /path/to/assembly.fasta
#                      -p /path/to/assembly_info.txt
#                      -o /path/to/output_folder
# -------------------------------------------------------------------


# Setup arguments
# ----------------------------------------------------------------------


@click.command()
@click.option(
    "--graph",
    "-g",
    required=True,
    help="path to the assembly graph file",
    type=click.Path(exists=True),
)
@click.option(
    "--contigs",
    "-c",
    required=True,
    help="path to the contigs file",
    type=click.Path(exists=True),
)
@click.option(
    "--paths",
    "-p",
    required=True,
    help="path to the contig paths file",
    type=click.Path(exists=True),
)
@click.option(
    "--hmmout",
    "-hm",
    required=True,
    help="path to the contig .hmmout file",
    type=click.Path(exists=True),
)
@click.option(
    "--phrogs",
    "-ph",
    required=True,
    help="path to the contig phrog annotations file",
    type=click.Path(exists=True),
)
@click.option(
    "--minlength",
    "-ml",
    default=2000,
    required=False,
    help="minimum length of circular contigs to consider",
    type=int,
)
@click.option(
    "--biglength",
    "-bl",
    default=10000,
    required=False,
    help="minimum length of a big circular contig",
    type=int,
)
@click.option(
    "--bigcount",
    "-bc",
    default=30,
    required=False,
    help="minimum contig count to be a complex component",
    type=int,
)
@click.option(
    "--pathdiff",
    "-pd",
    default=2000,
    required=False,
    help="length difference threshold to filter paths of a component",
    type=int,
)
@click.option(
    "--mgfrac",
    "-mgf",
    default=0.5,
    required=False,
    help="length threshold to consider single copy marker genes",
    type=float,
)
@click.option(
    "--alignscore",
    "-as",
    default=90,
    required=False,
    help="minimum alignment score (%) for phrog annotations",
    type=float,
)
@click.option(
    "--seqidentity",
    "-si",
    default=0.5,
    required=False,
    help="minimum sequence identity for phrog annotations",
    type=float,
)
@click.option(
    "--degree",
    "-d",
    default=10,
    required=False,
    help="minimum in/out degree of nodes in a component to be complex",
    type=int,
)
@click.option(
    "--output",
    "-o",
    required=True,
    help="path to the output folder",
    type=click.Path(exists=True),
)
def main(
    graph,
    contigs,
    paths,
    hmmout,
    phrogs,
    minlength,
    biglength,
    bigcount,
    pathdiff,
    mgfrac,
    alignscore,
    seqidentity,
    degree,
    output,
):

    """ds-bubbles: Resolve bacteriophage genomes from viral bubbles in metagenomic data."""

    # Setup logger
    # ----------------------------------------------------------------------

    logger = logging.getLogger("dsbubbles 0.1")
    logger.setLevel(logging.DEBUG)
    logging.captureWarnings(True)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    consoleHeader = logging.StreamHandler()
    consoleHeader.setFormatter(formatter)
    consoleHeader.setLevel(logging.INFO)
    logger.addHandler(consoleHeader)

    # Setup output path for log file
    fileHandler = logging.FileHandler(f"{output}/dsbubbles.log")
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

    logger.info(
        "Welcome to ds-bubbles: Resolve bacteriophage genomes from viral bubbles in metagenomic data."
    )

    logger.info(f"Input arguments: ")
    logger.info(f"Assembly graph file: {graph}")
    logger.info(f"Contigs file: {contigs}")
    logger.info(f"Contig paths file: {paths}")
    logger.info(f"Contig .hmmout file: {hmmout}")
    logger.info(f"Contig phrog annotations file: {phrogs}")
    logger.info(f"Minimum length of contigs to consider: {minlength}")
    logger.info(f"Minimum length of a big circular contig: {biglength}")
    logger.info(f"minimum contig count to be a complex component: {bigcount}")
    logger.info(
        f"Length difference threshold to filter paths of a component: {pathdiff}"
    )
    logger.info(f"Length threshold to consider single copy marker genes: {mgfrac}")
    logger.info(f"Minimum alignment score (%) for phrog annotations: {alignscore}")
    logger.info(f"Minimum sequence identity for phrog annotations: {seqidentity}")
    logger.info(
        f"Minimum in/out degree of nodes in a component to be complex: {degree}"
    )
    logger.info(f"Output folder: {output}")

    start_time = time.time()

    # Get assembly graph
    # ----------------------------------------------------------------------
    (
        assembly_graph,
        edge_list,
        contig_names,
        contig_names_rev,
        graph_contigs,
        edge_depths,
        self_looped_nodes,
        edges_lengths,
    ) = edge_graph_utils.build_assembly_graph(graph)

    logger.info(
        f"Total number of vertices in the assembly graph: {len(assembly_graph.vs)}"
    )
    logger.info(
        f"Total number of links in the assembly graph: {len(assembly_graph.es)}"
    )

    # Get circular contigs
    # ----------------------------------------------------------------------
    circular = edge_utils.get_circular(paths)

    # Get contigs with bacterial single copy marker genes
    # ----------------------------------------------------------------------
    smg_contigs, contig_smgs = gene_utils.get_smg_contigs(hmmout, mgfrac)

    # Get contigs with PHROGs
    # ----------------------------------------------------------------------
    contig_phrogs = gene_utils.get_phrog_contigs(phrogs, alignscore, seqidentity)

    # Get components with viral bubbles
    # ----------------------------------------------------------------------
    pruned_vs = component_utils.get_components(
        assembly_graph,
        contig_names,
        smg_contigs,
        contig_phrogs,
        circular,
        edges_lengths,
        minlength,
    )
    logger.info(f"Total number of components found: {len(pruned_vs)}")

    # Resolve genomes
    # ----------------------------------------------------------------------

    resolved_edges = set()

    all_resolved_paths = []

    all_components = []

    for my_count in tqdm(pruned_vs, desc="Resolving components"):

        my_genomic_paths = []

        logger.debug(f"my_count: {my_count}")

        candidate_nodes = pruned_vs[my_count]

        logger.debug(f"number of contigs: {len(candidate_nodes)}")

        pruned_graph = assembly_graph.subgraph(candidate_nodes)

        single_in_out_nodes = set()

        clean_max_degree = 0

        if len(candidate_nodes) > 1:

            has_long_circular = False

            # Check if the bubble is complex
            is_complex_graph = False

            all_degrees = []

            for node in candidate_nodes:

                # Get degree without self-looping nodes
                in_degree_node = len(
                    [
                        x
                        for x in assembly_graph.neighbors(node, mode="in")
                        if x not in self_looped_nodes
                    ]
                )
                out_degree_node = len(
                    [
                        x
                        for x in assembly_graph.neighbors(node, mode="out")
                        if x not in self_looped_nodes
                    ]
                )

                all_degrees.append(in_degree_node)
                all_degrees.append(out_degree_node)

                if in_degree_node == 1 or out_degree_node == 1:
                    single_in_out_nodes.add(node)

            clean_max_degree = max(all_degrees)

            for node in candidate_nodes:

                in_degree_node = assembly_graph.degree(node, mode="in")
                out_degree_node = assembly_graph.degree(node, mode="out")

                if (
                    out_degree_node > degree
                    or in_degree_node > degree
                    or len(candidate_nodes) >= bigcount
                ):
                    is_complex_graph = True

                contig_name = contig_names[node]

                if (
                    node in self_looped_nodes
                    and len(graph_contigs[contig_names[node]]) > biglength
                ):
                    has_long_circular = True
                    cycle_number = 1

                    path_string = graph_contigs[contig_name]

                    genome_path = GenomePath(
                        f"phage_comp_{my_count}_cycle_{cycle_number}",
                        [contig_names[candidate_nodes[0]]],
                        [candidate_nodes[0]],
                        path_string,
                        coverage,
                        len(graph_contigs[contig_name]),
                    )
                    my_genomic_paths.append(genome_path)

            if not has_long_circular:

                # Create Directed Graph
                G = nx.DiGraph()

                # Add a list of nodes:
                named_vertex_list = pruned_graph.vs()["label"]
                G.add_nodes_from(named_vertex_list)

                my_edges = []

                for edge in pruned_graph.es:
                    source_vertex_id = edge.source
                    target_vertex_id = edge.target
                    my_edges.append((source_vertex_id, target_vertex_id))

                # Add a list of edges:
                G.add_edges_from(my_edges)

                path_lengths = []
                path_coverages = []

                mypath_strings = []

                if is_complex_graph:
                    logger.debug("Complex_graph")
                    my_cycles = nx.cycle_basis(G.to_undirected())
                else:
                    logger.debug("Simple graph")
                    my_cycles = list(nx.simple_cycles(G))

                cycle_number = 1

                # Return a list of cycles described as a list of nodes
                for cycle in my_cycles:

                    if len(cycle) > 1:

                        total_length = 0

                        coverage = MAX_VAL

                        node_order = []
                        node_id_order = []

                        path_string = ""

                        for node in cycle:

                            contig_name = contig_names[candidate_nodes[node]]

                            resolved_edges.add(contig_names[candidate_nodes[node]])

                            node_order.append(contig_names[candidate_nodes[node]])
                            node_id_order.append(candidate_nodes[node])
                            total_length += len(graph_contigs[contig_name])
                            path_string += graph_contigs[contig_name]

                            if coverage > edge_depths[contig_name]:
                                coverage = edge_depths[contig_name]

                        path_lengths.append(total_length)
                        path_coverages.append(coverage)

                        mypath_strings.append(path_string)

                        # Save path

                        if (
                            len(path_string) > 0
                            and coverage != MAX_VAL
                            and coverage > 0
                        ):

                            if not is_complex_graph or (
                                is_complex_graph and len(path_string) > biglength
                            ):

                                genome_path = GenomePath(
                                    f"phage_comp_{my_count}_cycle_{cycle_number}",
                                    node_order,
                                    node_id_order,
                                    path_string,
                                    coverage,
                                    total_length,
                                )
                                my_genomic_paths.append(genome_path)

                        cycle_number += 1

        else:

            contig_name = contig_names[candidate_nodes[0]]

            resolved_edges.add(contig_name)

            path_string = graph_contigs[contig_name]

            cycle_number = 1

            genome_path = GenomePath(
                f"phage_comp_{my_count}_cycle_{cycle_number}",
                [contig_names[candidate_nodes[0]]],
                [candidate_nodes[0]],
                path_string,
                coverage,
                len(graph_contigs[contig_name]),
            )
            my_genomic_paths.append(genome_path)

        single_in_out_nodes_visited = set()
        single_in_out_nodes_visited_count = {}

        my_genomic_paths.sort(key=lambda x: x.length, reverse=True)

        final_genomic_paths = []

        if len(my_genomic_paths) > 1:

            # Get component stats
            graph_degree = assembly_graph.degree(candidate_nodes, mode="all")
            in_degree = assembly_graph.degree(candidate_nodes, mode="in")
            out_degree = assembly_graph.degree(candidate_nodes, mode="out")

            path_lengths = []
            path_coverages = []

            len_dif_threshold = pathdiff

            prev_length = my_genomic_paths[0].length

            for genomic_path in my_genomic_paths:
                current_len_dif = abs(prev_length - genomic_path.length)

                if current_len_dif < len_dif_threshold:

                    path_is_subset = False

                    for final_path in final_genomic_paths:
                        if set(genomic_path.node_order).issubset(
                            set(final_path.node_order)
                        ):
                            path_is_subset = True
                            break

                    for path_node in genomic_path.node_id_order:
                        if path_node in single_in_out_nodes_visited_count:
                            if (
                                single_in_out_nodes_visited_count[path_node]
                                >= clean_max_degree
                            ):
                                path_is_subset = True

                    if not path_is_subset:
                        prev_length = genomic_path.length

                        logger.debug(f"{genomic_path.id}\t{genomic_path.length}")
                        path_lengths.append(genomic_path.length)
                        path_coverages.append(genomic_path.coverage)
                        final_genomic_paths.append(genomic_path)
                        all_resolved_paths.append(genomic_path)

                        for path_node in genomic_path.node_id_order:
                            if path_node in single_in_out_nodes:
                                single_in_out_nodes_visited.add(path_node)

                                if path_node in single_in_out_nodes_visited_count:
                                    single_in_out_nodes_visited_count[path_node] += 1
                                else:
                                    single_in_out_nodes_visited_count[path_node] = 1

                else:
                    break

            genome_comp = GenomeComponent(
                f"phage_comp_{my_count}",
                len(candidate_nodes),
                len(final_genomic_paths),
                max(graph_degree),
                max(in_degree),
                max(out_degree),
                sum(graph_degree) / len(graph_degree),
                sum(in_degree) / len(in_degree),
                sum(out_degree) / len(out_degree),
                pruned_graph.density(loops=False),
                max(path_lengths),
                min(path_lengths),
                max(path_lengths) / min(path_lengths),
                path_lengths[path_coverages.index(max(path_coverages))],
                path_lengths[path_coverages.index(min(path_coverages))],
                path_lengths[path_coverages.index(max(path_coverages))]
                / path_lengths[path_coverages.index(min(path_coverages))],
                max(path_coverages),
                min(path_coverages),
                max(path_coverages) / min(path_coverages),
            )
            all_components.append(genome_comp)

        else:
            for genomic_path in my_genomic_paths:
                final_genomic_paths.append(genomic_path)
                all_resolved_paths.append(genomic_path)
                logger.debug(f"{genomic_path.id}\t{genomic_path.length}")

        # Write to file

        with open(f"{output}/resolved_paths.fasta", "a+") as myfile:

            for genomic_path in final_genomic_paths:

                myfile.write(f">{genomic_path.id}\n")

                chunks = [
                    genomic_path.path[i : i + FASTA_LINE_LEN]
                    for i in range(0, genomic_path.length, FASTA_LINE_LEN)
                ]

                for chunk in chunks:
                    myfile.write(f"{chunk}\n")

        output_genomes_path = f"{output}/resolved_phages"
        subprocess.run("mkdir -p " + output_genomes_path, shell=True)

        for genomic_path in final_genomic_paths:

            with open(
                f"{output}/resolved_phages/{genomic_path.id}.fasta", "w+"
            ) as myfile:

                myfile.write(">" + genomic_path.id + "\n")

                chunks = [
                    genomic_path.path[i : i + FASTA_LINE_LEN]
                    for i in range(0, genomic_path.length, FASTA_LINE_LEN)
                ]

                for chunk in chunks:
                    myfile.write(chunk + "\n")

    logger.info(f"Total number of genomes resolved: {len(all_resolved_paths)}")
    logger.info(f"Resolved genomes can be found in {output}/resolved_paths.fasta")

    # Record path information
    # ----------------------------------------------------------------------

    with open(f"{output}/resolved_genome_info.txt", "w") as myfile:
        myfile.write(f"Path\tCoverage\tLength\tNode order\n")
        for genomic_path in all_resolved_paths:
            myfile.write(
                f"{genomic_path.id}\t{genomic_path.coverage}\t{genomic_path.length}\t{genomic_path.node_order}\n"
            )

    logger.info(
        f"Resolved genome information can be found in {output}/resolved_genome_info.txt"
    )

    # Record component information
    # ----------------------------------------------------------------------

    with open(f"{output}/resolved_component_info.txt", "w") as myfile:
        myfile.write(f"Component\t")
        myfile.write(f"Number of nodes\t")
        myfile.write(f"Number of paths\t")
        myfile.write(f"Maximum degree\t")
        myfile.write(f"Maximum in degree\t")
        myfile.write(f"Maximum out degree\t")
        myfile.write(f"Average degree\t")
        myfile.write(f"Average in degree\t")
        myfile.write(f"Average out degree\t")
        myfile.write(f"Density\t")
        myfile.write(f"Maximum path length\t")
        myfile.write(f"Minimum path length\t")
        myfile.write(f"Length ratio (long/short)\t")
        myfile.write(f"Maximum coverage path length\t")
        myfile.write(f"Minimum coverage path length\t")
        myfile.write(f"Length ratio (highest cov/lowest cov)\t")
        myfile.write(f"Maximum coverage\t")
        myfile.write(f"Minimum coverage\t")
        myfile.write(f"Coverage ratio (highest/lowest)\n")

        for component in all_components:
            myfile.write(f"{component.id}\t")
            myfile.write(f"{component.n_nodes}\t")
            myfile.write(f"{component.n_paths}\t")
            myfile.write(f"{component.max_degree}\t")
            myfile.write(f"{component.max_in_degree}\t")
            myfile.write(f"{component.max_out_degree}\t")
            myfile.write(f"{component.avg_degree}\t")
            myfile.write(f"{component.avg_in_degree}\t")
            myfile.write(f"{component.avg_out_degree}\t")
            myfile.write(f"{component.density}\t")
            myfile.write(f"{component.max_path_length}\t")
            myfile.write(f"{component.min_path_length}\t")
            myfile.write(f"{component.min_max_len_ratio}\t")
            myfile.write(f"{component.max_cov_path_length}\t")
            myfile.write(f"{component.min_cov_path_length}\t")
            myfile.write(f"{component.min_max_cov_len_ratio}\t")
            myfile.write(f"{component.max_cov}\t")
            myfile.write(f"{component.min_cov}\t")
            myfile.write(f"{component.min_max_cov_ratio}\n")

    logger.info(
        f"Resolved component information can be found in {output}/resolved_component_info.txt"
    )

    # Get elapsed time
    # ----------------------------------------------------------------------

    # Determine elapsed time
    elapsed_time = time.time() - start_time

    # Print elapsed time for the process
    logger.info("Elapsed time: " + str(elapsed_time) + " seconds")

    # Exit program
    # ----------------------------------------------------------------------

    logger.info("Thank you for using ds-bubbles!")


if __name__ == "__main__":
    main()
