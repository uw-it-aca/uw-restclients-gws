# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from commonconf import override_settings


fdao_gws_override = override_settings(RESTCLIENTS_GWS_DAO_CLASS='Mock')
