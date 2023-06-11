import sys, os

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + "/../")

from easydags import ExecNode, DAG
import time
import networkx as nx


def test_running_ok():
    nodes = []

    def prepro():
        time.sleep(3)
        return "df with cool features"

    nodes.append(
        ExecNode(id_="pre_process", exec_function=prepro, output_name="my_cool_df")
    )

    def model1(**kwargs):
        df = kwargs["my_cool_df"]
        time.sleep(3)
        return "model 1 37803"

    nodes.append(
        ExecNode(
            id_="model1",
            exec_function=model1,
            depends_on_hard=["pre_process"],
            output_name="model1",
        )
    )

    def model2(**kwargs):
        df = kwargs["my_cool_df"]
        time.sleep(3)
        return "model 2 78373"

    nodes.append(
        ExecNode(
            id_="model2",
            exec_function=model2,
            depends_on_hard=["pre_process"],
            output_name="model2",
        )
    )

    def ensemble(**kwargs):
        model1 = kwargs["model1"]
        model2 = kwargs["model2"]
        result = f"{model1} and {model2}"
        return result

    nodes.append(
        ExecNode(
            id_="ensemble",
            exec_function=ensemble,
            depends_on_hard=["model1", "model2"],
            output_name="ensemble",
        )
    )

    dag = DAG(nodes, name="Ensemble test example", max_concurrency=3, debug=False)

    dag.execute()

    ids = list(dag.graph_ids)

    nodes_states = dag.node_dict

    states = [nodes_states[f].result["state"] for f in ids]

    assert min(states) == 1

    init_1 = nodes_states["model1"].result["initial_time"]
    init_2 = nodes_states["model2"].result["initial_time"]

    final_1 = nodes_states["model1"].result["final_time"]
    final_2 = nodes_states["model2"].result["final_time"]

    assert init_2 < final_1  # Assert parallel execution
    assert init_1 < final_2  # Assert parallel execution

    ### all nodes
    assert "pre_process" in dag.graph_ids.nodes
    assert "model1" in dag.graph_ids.nodes
    assert "model2" in dag.graph_ids.nodes
    assert "ensemble" in dag.graph_ids.nodes

    ### all edges

    assert ("model1", "ensemble") in dag.graph_ids.edges
    assert ("model2", "ensemble") in dag.graph_ids.edges
    assert ("pre_process", "model1") in dag.graph_ids.edges
    assert ("pre_process", "model2") in dag.graph_ids.edges
