# Replication Code

### It's Worth a Shot: Urban Density, Endogenous Vaccination Decisions, and Dynamics of Infectious Disease

This repository contains replication code for the paper by Andrew Souther, [Myong-Hun Chang](https://academic.csuohio.edu/changm/), and [Troy Tassier](https://sites.google.com/site/troytassier/home). 

You can find the published paper [here](https://link.springer.com/article/10.1007/s11403-022-00367-4). You can find the working paper version [in this repo](densityVax.pdf).  

For previous work by Chang and Tassier on agent-based models of vaccine coverage, [see here](https://link.springer.com/article/10.1007/s10614-019-09918-7).  

### Repo Structure

This repository has four directories: 

- `data_analysis`
- `deprecated`
- `simulation_code`
- `testing_files`

`data_analysis` is fairly self-contained. You can find all the raw data from our computational experiments in `data_files`. Running `Data Analysis Notebook` will generate pretty much all the plots and tables you can find in the paper. The only figures created outside that notebook are the network visualizations. We use [Gephi](https://gephi.org/) to generate those graphs. However, if you have Gephi, all the cleaned gexf files can be found in `network_data`. 

`deprecated` contains outdated code for a model we used in an early draft of the paper. All this code is written using a Python package called *mTree*, which is [under development at George Mason University](https://github.com/gmucsn).

`simulation_code` contains all the code necessary to run a simulation of your own using our model. In order to run an experiment, you must write a config file. You can find an example config file called `example_run.py`. Running that  Python file in a command line will automatically start a simulation. For each computational experiment we ran in the paper, you can find the corresponding config file in `config_files`. 

`testing_files` contains code for a series of preliminary tests we ran during the process of designing our agent decision-making model presented in the paper. This code is not so well-documented as the other directories. 

<!---
`sim_from_scratch` is a complete replication of `mtree_code` that avoids the use of *mTree.* if you want to replicate our computational experiments or play around with parameters of your own, this is where you should look. If you already have Python, it should be a fairly simple process. First, enter all your desired parameters into `run_sim.py` file. Then, make sure to install the Python package [jsonlines](https://jsonlines.readthedocs.io/en/latest/). Finally, place `run_sim.py` and `Vax_Model.py` in the same folder, and simply run the former (if you're using Windows, navigate to that folder in the Command Line, and type `python rum_sim.py`). 
-->





