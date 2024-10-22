from typing import Any, Dict, Optional, Tuple

from wandb.data_types import Table
from wandb.errors import Error


class Visualize:
    def __init__(self, id: str, data: Table) -> None:
        self._id = id
        self._data = data

    def get_config_value(self, key: str) -> Dict[str, Any]:
        return {
            "id": self._id,
            "historyFieldSettings": {"x-axis": "_step", "key": key},
        }

    @staticmethod
    def get_config_key(key: str) -> Tuple[str, str, str]:
        return "_wandb", "viz", key

    @property
    def value(self) -> Table:
        return self._data


class CustomChart:
    def __init__(
        self,
        id: str,
        data: Table,
        fields: Dict[str, Any],
        string_fields: Dict[str, Any],
        split_table: Optional[bool] = False,
    ) -> None:
        self._id = id
        self._data = data
        self._fields = fields
        self._string_fields = string_fields
        self._split_table = split_table

    def get_config_value(
        self,
        panel_type: str,
        query: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "panel_type": panel_type,
            "panel_config": {
                "panelDefId": self._id,
                "fieldSettings": self._fields,
                "stringSettings": self._string_fields,
                "transform": {"name": "tableWithLeafColNames"},
                "userQuery": query,
            },
        }

    @staticmethod
    def get_config_key(key: str) -> Tuple[str, str, str]:
        return "_wandb", "visualize", key

    @staticmethod
    def user_query(table_key: str) -> Dict[str, Any]:
        return {
            "queryFields": [
                {
                    "name": "runSets",
                    "args": [{"name": "runSets", "value": "${runSets}"}],
                    "fields": [
                        {"name": "id", "fields": []},
                        {"name": "name", "fields": []},
                        {"name": "_defaultColorIndex", "fields": []},
                        {
                            "name": "summaryTable",
                            "args": [{"name": "tableKey", "value": table_key}],
                            "fields": [],
                        },
                    ],
                }
            ],
        }

    @property
    def table(self) -> Table:
        return self._data

    @property
    def fields(self) -> Dict[str, Any]:
        return self._fields

    @property
    def string_fields(self) -> Dict[str, Any]:
        return self._string_fields


def custom_chart(
    vega_spec_name: str,
    data_table: Table,
    fields: Dict[str, Any],
    string_fields: Optional[Dict[str, Any]] = None,
    split_table: Optional[bool] = False,
) -> CustomChart:
    if string_fields is None:
        string_fields = {}
    if not isinstance(data_table, Table):
        raise Error(
            f"Expected `data_table` to be `wandb.Table` type, instead got {type(data_table).__name__}"
        )
    return CustomChart(
        id=vega_spec_name,
        data=data_table,
        fields=fields,
        string_fields=string_fields,
        split_table=split_table,
    )


def visualize(id: str, value: Table) -> Visualize:
    if not isinstance(value, Table):
        raise Error(
            f"Expected `value` to be `wandb.Table` type, instead got {type(value).__name__}"
        )
    return Visualize(id=id, data=value)


def _visualization_hack(run, row: dict[str, Any]) -> dict[str, Any]:
    chart_keys = set()
    split_table_set = set()
    for k in row:
        if isinstance(row[k], Visualize):
            key = row[k].get_config_key(k)
            value = row[k].get_config_value(k)
            row[k] = row[k]._data
            run._config_callback(val=value, key=key)
        elif isinstance(row[k], CustomChart):
            chart_keys.add(k)
            key = row[k].get_config_key(k)
            if row[k]._split_table:
                value = row[k].get_config_value(
                    "Vega2", row[k].user_query(f"Custom Chart Tables/{k}_table")
                )
                split_table_set.add(k)
            else:
                value = row[k].get_config_value(
                    "Vega2", row[k].user_query(f"{k}_table")
                )
            row[k] = row[k]._data
            run._config_callback(val=value, key=key)

    for k in chart_keys:
        # remove the chart key from the row
        # TODO: is this really the right move? what if the user logs
        #     a non-custom chart to this key?
        if k in split_table_set:
            row[f"Custom Chart Tables/{k}_table"] = row.pop(k)
        else:
            row[f"{k}_table"] = row.pop(k)
    return row
