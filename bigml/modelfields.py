# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Copyright 2013-2014 BigML
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A BasicModel resource.

This module defines a BasicModel to hold the main information of the model
resource in BigML. It becomes the starting point for the Model class, that
is used for local predictions.

"""
import logging
LOGGER = logging.getLogger('BigML')

from bigml.util import invert_dictionary


def extract_objective(objective_field):
    """Extract the objective field id from the model structure

    """
    if isinstance(objective_field, list):
        return objective_field[0]
    return objective_field



def check_model_structure(model):
    """Checks the model structure to see if it contains all the needed keys

    """
    return (isinstance(model, dict) and 'resource' in model and
            model['resource'] is not None and
            ('object' in model and 'model' in model['object'] or
             'model' in model))


class ModelFields(object):
    """ A lightweight wrapper of the field information in the model or cluster
        objects

    """

    def __init__(self, fields, objective_id=None):
        if isinstance(fields, dict):
            try:
                self.objective_id = objective_id
                self.uniquify_varnames(fields)
                self.inverted_fields = invert_dictionary(fields)
                self.fields = {}
                self.fields.update(fields)
            except KeyError:
                raise Exception("Wrong field structure.")

    def uniquify_varnames(self, fields):
        """Tests if the fields names are unique. If they aren't, a
           transformation is applied to ensure unicity.

        """
        unique_names = set([fields[key]['name'] for key in fields])
        if len(unique_names) < len(fields):
            self.transform_repeated_names(fields)

    def transform_repeated_names(self, fields):
        """If a field name is repeated, it will be transformed adding its
           column number. If that combination is also a field name, the
           field id will be added.

        """
        # The objective field treated first to avoid changing it.
        if self.objective_id:
            unique_names = [fields[self.objective_id]['name']]
        else:
            unique_names = []

        field_ids = [field_id for field_id in fields
                     if not self.objective_id or field_id != self.objective_id]
        for field_id in field_ids:
            new_name = fields[field_id]['name']
            if new_name in unique_names:
                new_name = "{0}{1}".format(fields[field_id]['name'],
                                           fields[field_id]['column_number'])
                if new_name in unique_names:
                    new_name = "{0}_{1}".format(new_name, field_id)
                fields[field_id]['name'] = new_name
            unique_names.append(new_name)

    def filter_input_data(self, input_data, by_name=True):
        """Filters the keys given in input_data checking against model fields

        """

        if isinstance(input_data, dict):
            empty_fields = [(key, value) for (key, value) in input_data.items()
                            if value is None]
            for (key, value) in empty_fields:
                del input_data[key]

            if by_name:
                # We no longer check that the input data keys match some of
                # the dataset fields. We only remove the keys that are not
                # used as predictors in the model
                input_data = dict(
                    [[self.inverted_fields[key], value]
                     for key, value in input_data.items()
                     if key in self.inverted_fields])
            else:
                input_data = dict(
                    [[key, value]
                     for key, value in input_data.items()
                     if key in self.fields])
            return input_data
        else:
            LOGGER.error("Failed to read input data in the expected"
                         " {field:value} format.")
            return {}
