# Replication Code

### "It's Worth a Shot: Urban Density, Endogenous Vaccination Decisions, and Dynamics of Infectious Disease"

This repository contains replication code for the above-titled working paper by Tassier, Chang, and Souther. You can find a draft of the paper [here](densityVax.pdf).  

For previous work by [Myong-Hun Chang](https://academic.csuohio.edu/changm/) and [Troy Tassier](https://sites.google.com/site/troytassier/home) on agent-based models of vaccine coverage, [see here](https://link.springer.com/article/10.1007/s10614-019-09918-7).  

### Repo Structure

This repository has three directories: 

- `data_analysis`
- `mtree_code` 
- `sim_from_scratch`

`data_analysis` is fairly self-contained. You can find all the raw data from our computational experiments in `experiment_data_logs`. Running `Data Analysis Notebook` will generate pretty much all the plots and tables you can find in the paper. The only figures created outside that notebook are the network visualizations. We use [Gephi](https://gephi.org/) to generate those graphs. However, if you have Gephi, all the cleaned gexf files can be found in `network_data`. 

`mtree_code` is not so self-contained. While preparing our paper, we ran all computational experiments using the Python package *mTree*, which is [under development at George Mason University](https://github.com/gmucsn). If you want to run these files, you'll have to install a particular version of *mTree*, and the documentation for this package is still a work in progress. I suggest looking at the next paragraph if you are curious about re-running our agent-based simulations from scratch. 

`sim_from_scratch` is a complete replication of `mtree_code` that avoids the use of *mTree.* if you want to replicate our computational experiments or play around with parameters of your own, this is where you should look. If you already have Python, it should be a fairly simple process. First, enter all your desired parameters into `run_sim.py` file. Then, make sure to install the Python package [jsonlines](https://jsonlines.readthedocs.io/en/latest/). Finally, place `run_sim.py` and `Vax_Model.py` in the same folder, and simply run the former (if you're using Windows, navigate to that folder in the Command Line, and type `python rum_sim.py`). 




