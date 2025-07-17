**obsidiantools in 15 minutes**

# Libraries and config


```python
# built-in libs
import os
from pathlib import Path

# obsidiantools requirements
import numpy as np
import pandas as pd
import networkx as nx

# extra libs for this notebook (visualise graph)
import matplotlib.pyplot as plt
%matplotlib inline
```


```python
!pip show obsidiantools
```

    Name: obsidiantools
    Version: 0.10.0
    Summary: Obsidian Tools - a Python interface for Obsidian.md vaults
    Home-page: https://github.com/mfarragher/obsidiantools
    Author: Mark Farragher
    Author-email: 
    License: BSD
    Location: /home/mark/miniconda3/envs/obsidian/lib/python3.11/site-packages
    Requires: beautifulsoup4, bleach, html2text, lxml, markdown, networkx, numpy, pandas, pymdown-extensions, python-frontmatter
    Required-by: 


## Vault directory


```python
VAULT_DIR = Path(os.getcwd()) / 'vault-stub'
```


```python
VAULT_DIR.exists()
```




    True



## Obsidian tools


```python
import obsidiantools.api as otools  # api shorthand
```

# Explore your vault

## Simple one-liner for setup 😎

The `Vault` class is the object you need for exploring your vault.  Set up the object with the path to your directory.

- **CONNECT** is the method for connecting all your vault notes in a graph.
    - Once called, you will be able to access metadata and do analysis of your notes.
    - This needs to be called to get the essential structure of your vault, e.g. lookups for your notes, getting wikilinks, backlinks, etc.
- **GATHER** is the method for gathering all your vault notes' content.
    - Once called, you will be able to get plaintext content of individual notes and a master index of notes.
    - This needs to be called to get the content of your notes.  There is config that can be specified in the function, e.g. whether to keep code blocks.


```python
vault = otools.Vault(VAULT_DIR).connect().gather()
```

Attributes that says whether the main methods are called:


```python
print(f"Connected?: {vault.is_connected}")
print(f"Gathered?:  {vault.is_gathered}")
```

    Connected?: True
    Gathered?:  True


Attribute that stores the location of your vault


```python
vault.dirpath
```




    PosixPath('/home/mark/Github/obsidiantools-demo/vault-stub')



## Tell me about my vault...

### 1. What files do I have in my vault?


```python
vault.md_file_index
```




    {'Sussudio': PosixPath('Sussudio.md'),
     'Isolated note': PosixPath('Isolated note.md'),
     'Brevissimus moenia': PosixPath('lipsum/Brevissimus moenia.md'),
     'Ne fuit': PosixPath('lipsum/Ne fuit.md'),
     'Alimenta': PosixPath('lipsum/Alimenta.md'),
     'Vulnera ubera': PosixPath('lipsum/Vulnera ubera.md'),
     'lipsum/Isolated note': PosixPath('lipsum/Isolated note.md'),
     'Causam mihi': PosixPath('lipsum/Causam mihi.md')}



If you want to filter on subdirectories, you can do so like this:


```python
(otools.Vault(VAULT_DIR, include_subdirs=['lipsum'], include_root=False)
 .md_file_index)
```




    {'Brevissimus moenia': PosixPath('lipsum/Brevissimus moenia.md'),
     'Ne fuit': PosixPath('lipsum/Ne fuit.md'),
     'Alimenta': PosixPath('lipsum/Alimenta.md'),
     'Vulnera ubera': PosixPath('lipsum/Vulnera ubera.md'),
     'Isolated note': PosixPath('lipsum/Isolated note.md'),
     'Causam mihi': PosixPath('lipsum/Causam mihi.md')}



### 2. Which notes are 'isolated' in my vault?

In graph analysis, nodes are **isolated** if they do not connect to other nodes in a graph.  Each NOTE in your vault in graph terminology is a node.

In the Obsidian world, what does it mean for notes to be isolated?

**Isolated notes** have **no backlinks** AND **no wikilinks**.


```python
vault.isolated_notes
```




    ['Isolated note', 'lipsum/Isolated note']



In the Obsidian community these notes are often called 'orphan notes'.  This interface is sticking to graph analysis terminology; NetworkX calls the graph nodes 'isolates'.

### 3. Which notes have I not got round to creating yet?

When you create wikilinks in your vault notes, you can create connections to notes that you haven't created yet.  This means that these new notes have backlinks and are displayed in your vault graph, but they don't exist as markdown files.

In this interface these are called **nonexistent notes**.


```python
vault.nonexistent_notes
```




    ['Caelum',
     'Aras Teucras',
     'Tarpeia',
     'Vita',
     'Dives',
     'Virtus',
     'Bacchus',
     'Tydides',
     'Manus',
     'Amor',
     'Aetna',
     'American Psycho (film)']



### 4. What are the notes that have the most backlinks?

The **`get_note_metadata`** method gives a summary of your vault's notes.

You can see, for example:
- Counts of backlinks (`n_backlinks`)
- Counts of wikilinks (`n_wikilinks`)
- Counts of embedded files (`n_embedded_files`)
- Modified time (`modified_time`)

Note: created time is available across all operating systems so that is not included.


```python
df = vault.get_note_metadata()
```


```python
df.info()
```

    <class 'pandas.core.frame.DataFrame'>
    Index: 20 entries, Caelum to Brevissimus moenia
    Data columns (total 8 columns):
     #   Column            Non-Null Count  Dtype         
    ---  ------            --------------  -----         
     0   rel_filepath      8 non-null      object        
     1   abs_filepath      8 non-null      object        
     2   note_exists       20 non-null     bool          
     3   n_backlinks       20 non-null     int64         
     4   n_wikilinks       8 non-null      float64       
     5   n_tags            8 non-null      float64       
     6   n_embedded_files  8 non-null      float64       
     7   modified_time     8 non-null      datetime64[ns]
    dtypes: bool(1), datetime64[ns](1), float64(3), int64(1), object(2)
    memory usage: 1.3+ KB


Sort these notes by number of backlinks (descending order).


```python
df.sort_values('n_backlinks', ascending=False)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>rel_filepath</th>
      <th>abs_filepath</th>
      <th>note_exists</th>
      <th>n_backlinks</th>
      <th>n_wikilinks</th>
      <th>n_tags</th>
      <th>n_embedded_files</th>
      <th>modified_time</th>
    </tr>
    <tr>
      <th>note</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Bacchus</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>5</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Caelum</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>3</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Vita</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>3</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Tarpeia</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>3</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Manus</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>3</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Ne fuit</th>
      <td>lipsum/Ne fuit.md</td>
      <td>/home/mark/Github/obsidiantools-demo/vault-stu...</td>
      <td>True</td>
      <td>2</td>
      <td>6.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2022-12-24 16:28:38.878715754</td>
    </tr>
    <tr>
      <th>Amor</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>2</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Aetna</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>1</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Virtus</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>1</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Dives</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>1</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Brevissimus moenia</th>
      <td>lipsum/Brevissimus moenia.md</td>
      <td>/home/mark/Github/obsidiantools-demo/vault-stu...</td>
      <td>True</td>
      <td>1</td>
      <td>3.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2021-09-11 10:12:14.793214083</td>
    </tr>
    <tr>
      <th>Aras Teucras</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>1</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>American Psycho (film)</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>1</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Tydides</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>False</td>
      <td>1</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaT</td>
    </tr>
    <tr>
      <th>Causam mihi</th>
      <td>lipsum/Causam mihi.md</td>
      <td>/home/mark/Github/obsidiantools-demo/vault-stu...</td>
      <td>True</td>
      <td>1</td>
      <td>4.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2022-12-22 19:53:47.862288952</td>
    </tr>
    <tr>
      <th>Alimenta</th>
      <td>lipsum/Alimenta.md</td>
      <td>/home/mark/Github/obsidiantools-demo/vault-stu...</td>
      <td>True</td>
      <td>0</td>
      <td>12.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2023-01-04 20:29:50.775411367</td>
    </tr>
    <tr>
      <th>lipsum/Isolated note</th>
      <td>lipsum/Isolated note.md</td>
      <td>/home/mark/Github/obsidiantools-demo/vault-stu...</td>
      <td>True</td>
      <td>0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2022-12-24 16:28:38.878715754</td>
    </tr>
    <tr>
      <th>Sussudio</th>
      <td>Sussudio.md</td>
      <td>/home/mark/Github/obsidiantools-demo/vault-stu...</td>
      <td>True</td>
      <td>0</td>
      <td>1.0</td>
      <td>5.0</td>
      <td>2.0</td>
      <td>2022-12-28 15:07:18.529378891</td>
    </tr>
    <tr>
      <th>Isolated note</th>
      <td>Isolated note.md</td>
      <td>/home/mark/Github/obsidiantools-demo/vault-stu...</td>
      <td>True</td>
      <td>0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2022-12-28 15:07:44.668570757</td>
    </tr>
    <tr>
      <th>Vulnera ubera</th>
      <td>lipsum/Vulnera ubera.md</td>
      <td>/home/mark/Github/obsidiantools-demo/vault-stu...</td>
      <td>True</td>
      <td>0</td>
      <td>3.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2022-12-22 21:22:04.807774067</td>
    </tr>
  </tbody>
</table>
</div>



We can see that **Bacchus** has the most backlinks.  It's actually a nonexistent note.


```python
vault.get_backlinks('Bacchus')
```




    ['Ne fuit', 'Alimenta', 'Alimenta', 'Alimenta', 'Alimenta']




```python
vault.get_backlink_counts('Bacchus')
```




    {'Ne fuit': 1, 'Alimenta': 4}



You can see all the backlinks in the `backlinks_index`.


```python
vault.backlinks_index
```




    {'Sussudio': [],
     'Isolated note': [],
     'Brevissimus moenia': ['Alimenta'],
     'Ne fuit': ['Alimenta', 'Causam mihi'],
     'Alimenta': [],
     'Vulnera ubera': [],
     'lipsum/Isolated note': [],
     'Causam mihi': ['Ne fuit'],
     'American Psycho (film)': ['Sussudio'],
     'Tarpeia': ['Brevissimus moenia', 'Alimenta', 'Vulnera ubera'],
     'Caelum': ['Brevissimus moenia', 'Ne fuit', 'Vulnera ubera'],
     'Vita': ['Brevissimus moenia', 'Alimenta', 'Vulnera ubera'],
     'Aras Teucras': ['Ne fuit'],
     'Manus': ['Ne fuit', 'Alimenta', 'Causam mihi'],
     'Bacchus': ['Ne fuit', 'Alimenta', 'Alimenta', 'Alimenta', 'Alimenta'],
     'Amor': ['Ne fuit', 'Alimenta'],
     'Virtus': ['Alimenta'],
     'Tydides': ['Alimenta'],
     'Dives': ['Causam mihi'],
     'Aetna': ['Causam mihi']}



Similar functionality exists in the API for wikilinks (e.g. `wikilinks_index`, `get_wikilinks`)

What are the embedded files in Sussudio?


```python
vault.get_embedded_files('Sussudio')
```




    ['Sussudio.mp3', '1999.flac']



### 5. What are the tags and front matter in notes?

By default the embedded files are not shown in the Obsidian graph, but there is an option to show them in the graph of a vault.  Currently that capability is not supported in `obsidiantools`; only the default behaviour is supported.

Load the front matter for Sussudio parsed as a dict:


```python
vault.get_front_matter('Sussudio')
```




    {'title': 'Sussudio',
     'artist': 'Phil Collins',
     'category': 'music',
     'year': 1985,
     'url': 'https://www.discogs.com/Phil-Collins-Sussudio/master/106239',
     'references': [[['American Psycho (film)']], 'Polka Party!'],
     'chart_peaks': [{'US': 1}, {'UK': 12}]}



In Sussudio note, the tag `#y1982` appears twice.  The order of appearance in their output from `get_tags()` is based on their order in the note content:


```python
vault.get_tags('Sussudio')
```




    ['y1982', 'y_1982', 'y-1982', 'y1982', 'y2000']



## Visualise your vault

The Obsidian app should be where you explore your vault visually, for all the interactive benefits!

If you want to do network analysis of your vault, or else focus on a subgraph, then you can do analysis through the NetworkX graph object: `vault.graph`

Use the **`get_all_file_metadata`** method to get data on all files.  For this notebook, it will just show notes.


```python
df_all = vault.get_all_file_metadata()
```

    /home/mark/miniconda3/envs/obsidian/lib/python3.11/site-packages/obsidiantools/api.py:1343: UserWarning: Only notes (md files) were used to build the graph.  Set attachments=True in the connect method to show all file metadata.
      warnings.warn('Only notes (md files) were used to build the graph.  Set attachments=True in the connect method to show all file metadata.')



```python
# graph colour info
colour_map = {'note': '#826ED9',
              'nonexistent': '#D3D3D3',
              'attachment': '#D6D470'}
node_colours_lookup = (df_all['graph_category']
                       .map(colour_map)
                       .to_dict())
node_colours_list = [node_colours_lookup.get(i)
                     for i in vault.graph.nodes()]
```

This in the legend for how nodes in the graph will appear in the visualisation:
- <span><img src="https://via.placeholder.com/15/826ED9/000000?text=+#left" alt="alt_text" align="left"/>: Note exists as a file</span>
- <span><img src="https://via.placeholder.com/15/D3D3D3/000000?text=+#left" alt="alt_text" align="left"/>: File doesn't exist</span>

_Attachment files are shown in another notebook, but the code above for graph colours works for however you set up your notes._


```python
fig, ax = plt.subplots(figsize=(13,7))
nx.draw(vault.graph, node_color=node_colours_list, with_labels=True, ax=ax)
ax.set_title('Vault graph')
plt.show()
```


    
![png](obsidiantools_in_15_minutes_files/obsidiantools_in_15_minutes_54_0.png)
    


### Graph analysis

Where `obsidiantools` has the potential to be really powerful in your Obsidian workflows is its linkage with the sophisticated graph analysis capabilities of NetworkX.

There are many algorithms that you can use to analyse the **centrality** of nodes in a graph in NetworkX.

Let's look at the **PageRank** of notes in the vault.  Google has used PageRank to rank the importance of search engine results.

As outlined by Google:

>The underlying assumption is that more important websites are likely to receive more links from other websites

In the **Obsidian** realm, the notes that would be ranked highest by PageRank are the 'notes likely to receive more links from other notes', i.e. the notes that have **backlinks from a broad range of notes**.

Let's see this in action.


```python
(pd.Series(nx.pagerank(vault.graph), name='pagerank')
 .sort_values(ascending=False))
```




    American Psycho (film)    0.072282
    Caelum                    0.069320
    Tarpeia                   0.064764
    Vita                      0.064764
    Manus                     0.059022
    Bacchus                   0.057465
    Ne fuit                   0.051698
    Amor                      0.049163
    Dives                     0.048930
    Aetna                     0.048930
    Causam mihi               0.046395
    Aras Teucras              0.046395
    Virtus                    0.041839
    Tydides                   0.041839
    Brevissimus moenia        0.041839
    Isolated note             0.039071
    lipsum/Isolated note      0.039071
    Vulnera ubera             0.039071
    Alimenta                  0.039071
    Sussudio                  0.039071
    Name: pagerank, dtype: float64



- `Caelum` has the highest rank in the main graph.  It has 3 backlinks from 3 notes.
- These notes have 0 backlinks and rank very low as a result:
    - `Isolated note` (of course!)
    - `Vulnera ubera`
    - `Alimenta`
    - `Sussudio`
- `Bacchus` has the most backlinks (5), but doesn't rank highest!  Why might that be?  Well, the quality of those backlinks are questionable.  There are 4 backlinks to the note from `Alimenta`, which has 0 backlinks.  See further analysis below on what those backlinks look like.

## Get text

The API splits out the text into two:
- **Source text:** `source_text_index` contains text across the files in a format that tries to represent how it is stored inthe files.  Formatting is preserved as much as possible, it keeps math and full link information, etc.
- **Readable text:** `readable_text_index` contains text across the files in a format that minimises the formatting, so that it can be used easily for NLP analysis.

### Source text

Look at the last 5 lines for `Alimenta`.

#### Low-quality backlinks

This is a peek at the plaintext of the files, which are only accessible after the GATHER function is called.  All the text is stored in the `text_index` of the vault.


```python
last_lines_alimenta = (vault.get_source_text('Alimenta')
                       .splitlines()[-5:])
```


```python
for l in last_lines_alimenta:
    print(l)
```

    Metuunt conspecta [[Tydides]] famem, et **Phryges vix est** color tu aut. Tellure atque laudaret! Eo certum rupta, cur tum latere premit qui pariter aureus? Pulcherrime dolor postquam. Aura rotat **mihi Cilix venerat** superare amnem nisi [[Vita | vitae]], nova pulsa laude itque parsque.
    
    ## More wikilinks
    
    [[Bacchus]] [[Bacchus]] [[Bacchus]]


Here we can see that there are a few repetitive wikilinks to `Bacchus` at the end of the file.  As it happens, all the other notes in this vault only link to another note once.  This is where the quality of backlinks matter to PageRank: notes don't rank high if they pile up backlinks from one note.

### Readable text

When using the 'readable text', notice:
- The wikilink `[[Vita | vitae]]` has become `vitae`, to reflect how the text would be rendered in the reading mode of Obsidian.
- Bold formatting from text, e.g. `**Phryges vix est**`, has been removed.


```python
last_lines_readable_alimenta = (vault.get_readable_text('Alimenta')
                                .splitlines()[-5:])
```


```python
for l in last_lines_readable_alimenta:
    print(l)
```

    Metuunt conspecta Tydides famem, et Phryges vix est color tu aut. Tellure atque laudaret! Eo certum rupta, cur tum latere premit qui pariter aureus? Pulcherrime dolor postquam. Aura rotat mihi Cilix venerat superare amnem nisi vitae, nova pulsa laude itque parsque.
    
    ## More wikilinks
    
    Bacchus Bacchus Bacchus

