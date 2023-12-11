# `.pysplit` files

The form of a `.pysplit` file defined by the following:

```
{
    version: string
    game: string
    category: string
    splitNames: list[string]
    defaultComparisons: {
        bestSegments: Comparison
        bestRun: Comparison
    }
    customComparisons: list[Comparison]
    runs: list[Run]
}
```

with the following auxiliary types:

```
Comparison:
    name: string
    segments: list[Time]
    totals: list[Time]

Run:
    startTime: IsoTime
    endTime: IsoTime
    segments: list[Time]
    totals: list[Time]

Time: "(%H:)?(%M:)?%S.xxxxx" | "-"

IsoTime: iso-formatted time (%Y-%M-%dT%H:%M:%S.%f(%z)?)
```

An example is shown in `example.pysplit`.

# Layout example

`layout.json` is an example of a layout (it's the one I am using
currently). Note that not all the components have a configuration
associated with them - the components with no set configuration use
the default configuration in its entirety. It should be stored in
the `layouts` directory so it has the path 
`layouts/<layout name>.json`. For example, my layout is stored at 
`layouts/default.json`.

`detailedTimer.json` is an example of a component configuration
file. It should be stored in the `config` directory so it has the
path `config/detailedTimer.json` (the component loader only looks
in the `config` directory for user configuration files).

Notice (by comparison with `defaults/detailedTimer.json`)
that not all the values required are defined explicitly in the
component example. Any values that are not specified in the user
configuration will be filled in with the values in
`defaults/detailedTimer.json`.
