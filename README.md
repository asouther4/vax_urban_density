# Replication Code

### "It's Worth a Shot: Urban Density, Endogenous Vaccination Decisions, and Dynamics of Infectious Disease"

This repository contains replication code for the above-titled working paper by Tassier, Chang, and Souther (2020). Paper coming soon!!

For previous work by [Myong-Hun Chang](https://academic.csuohio.edu/changm/) and [Troy Tassier](https://sites.google.com/site/troytassier/home) on agent-based models of vaccine coverage, [see here](https://idp.springer.com/authorize/casa?redirect_uri=https://link.springer.com/content/pdf/10.1007/s10614-019-09918-7.pdf&casa_token=YcKmIno4UWcAAAAA:k3JNvB9KoLsvrR8mct_02xxDK59pQsS-9NIbN7g8kw7EsHfs660-Z17LmVfL4YA8rwuJJN0rIWHIv41P7g).  

### Repo Structure

This repository has two directories: 

- `data_analysis`
- `sim_code` 

`data_analysis` is fairly self-contained. You can find all the raw data from our computational experiments in `experiment_data_logs`. Running `Data Analysis Notebook` will generate pretty much all the plots and tables you can find in the paper. 

The only figures created outside that notebook are the network visualizations. We use [Gephi](https://gephi.org/) to generate those graphs. However, if you have Gephi, all the cleaned gexf files can be found in `network_data`. 


`sim_code` is not so self-contained. If you want to replicate our agent-based simulations from scratch, you'll have to install a particular version of a Python package called *mTree* which is [under development at George Mason University](https://github.com/gmucsn). Depending on your hardware, it will also take a few hours to run simulations of any considerable size. 

If neither of those two facts deter you and you are still curious about our agent-based simulation, feel free to email me! asouther@fordham.edu


