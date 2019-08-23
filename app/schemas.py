from graphql import (
    graphql,
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLInputObjectType,
    GraphQLField,
    GraphQLInputObjectField,
    GraphQLNonNull,
    GraphQLString,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLEnumValue,
    GraphQLEnumType,
    GraphQLArgument,
    GraphQLFloat
)

from .fixtures import (
    postPredictionJobs,
    getItemSearch
)

itemTypeEnum = GraphQLEnumType(
    "ItemType",
    description="Possible types of searches for items.",
    values={
        "PROTEIN": GraphQLEnumValue(0, description="Protein item."),
        "DNA": GraphQLEnumValue(1, description="DNA item."),
        "RNA": GraphQLEnumValue(2, description="RNA item."),
        "NA": GraphQLEnumValue(3, description="Other nucleic acid item."),
        "LIGAND": GraphQLEnumValue(4, description="Ligand molecule item.")
    }
)

searchTypeEnum = GraphQLEnumType(
    "SearchType",
    description="Possible types of searches for items.",
    values={
        "TERM": GraphQLEnumValue(5, description="Search by term on RCSB (first chosen)."),
        "IDCHAIN": GraphQLEnumValue(6, description="Search by PDB ID/Chain or Chemical ID on RCSB."),
        "SEQUENCE": GraphQLEnumValue(7, description="Prewritten sequence.")
    }
)

itemInputType = GraphQLInputObjectType(
    name="ItemInput",
    fields={
        "sequence": GraphQLInputObjectField(GraphQLNonNull(GraphQLString), description="Sequence of item."),
        "itemType": GraphQLInputObjectField(GraphQLNonNull(itemTypeEnum), description="The type of item.")
    }
)

searchInputType = GraphQLInputObjectType(
    name="SearchInput",
    fields={
        "searchTerm": GraphQLInputObjectField(GraphQLNonNull(GraphQLString), description="Search term for item."),
        "itemType": GraphQLInputObjectField(GraphQLNonNull(itemTypeEnum), description="The type of item."),
        "searchType": GraphQLInputObjectField(GraphQLNonNull(searchTypeEnum), description="The type of item.")
    }
)

predictionInputType = GraphQLInputObjectType(
    name="PredictionInput",
    fields={
        "predictionType": GraphQLInputObjectField(GraphQLNonNull(GraphQLString), description="The type of prediction."),
        "item1": GraphQLInputObjectField(GraphQLNonNull(itemInputType), description="Primary item to predict against."),
        "item2": GraphQLInputObjectField(itemInputType, description="Optional secondary item to predict against.")
    }
)

itemResultType = GraphQLObjectType(
    "ItemResult",
    fields=lambda: {
        "searchTerm": GraphQLField(GraphQLNonNull(searchTypeEnum), description="Search term for item."),
        "itemType": GraphQLField(GraphQLNonNull(itemTypeEnum), description="The type of item."),
        "searchType": GraphQLField(GraphQLNonNull(GraphQLString), description="The type of search."),
        "sequence": GraphQLField(GraphQLNonNull(GraphQLString), description="Sequence of item.")
    }
)

predictionType = GraphQLObjectType(
    "Prediction",
    fields=lambda: {
        "predictionType": GraphQLField(GraphQLNonNull(GraphQLString), description="Type of prediction."),
        "item1": GraphQLField(GraphQLNonNull(itemType), description="Primary item predicted against."),
        "item2": GraphQLField(itemType, description="Optional secondary item predicted against."),
        "result": GraphQLField(GraphQLNonNull(GraphQLList(GraphQLFloat)), description="List of results of prediction.")
    }
)

queryType = GraphQLObjectType(
    "Query",
    fields=lambda: {
        "predictions": GraphQLField(
            GraphQLList(GraphQLString),
            args={
                "pairs": GraphQLArgument(
                    description="Pairs of item inputs for prediction.",
                    type=GraphQLNonNull(GraphQLList(predictionInputType))
                )
            },
            resolver=lambda root, info, **args: postPredictionJobs(args["pairs"])
        ),
        "search": GraphQLField(
            GraphQLList(GraphQLString),
            args={
                "items": GraphQLArgument(
                    description="Item inputs for searching sequences/smiles.",
                    type=GraphQLNonNull(GraphQLList(searchInputType))
                )
            },
            resolver=lambda root, info, **args: getItemSearch(args["items"])
        )
    }
)

predictSchema = GraphQLSchema(query=queryType, types=[itemInputType, predictionInputType])
