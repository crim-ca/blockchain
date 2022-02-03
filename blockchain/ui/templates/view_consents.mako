<%inherit file="body.mako"/>
<%include file="node_info.mako"/>
<%include file="chain_info.mako"/>
<%namespace name="utils" file="utils.mako"/>
<script>
    <%include file="utils.js"/>
</script>


<%def name="render_subsystem(subsystem)">
    %for field in subsystem_fields:
        <td class="subsystem-field collapsible">
            ${utils.get_styled_value(subsystem.get(field), field)}
        </td>
    %endfor
</%def>


<div class="consents">
    <div class="consents-status">
        <table>
            <thead>
                <tr><th colspan="2">Statuses</th></tr>
            </thead>
            <tbody>
                <tr><td>Updated:</td>   <td>${utils.get_styled_value(updated, "datetime")}</td></tr>
                <tr><td>Outdated:</td>  <td>${utils.get_styled_value(outdated, "bool")}</td></tr>
                <tr><td>Verified:</td>  <td>${utils.get_styled_value(verified, "bool")}</td></tr>
            </tbody>
        </table>
    </div>
    <div class="consents-latest">
        <table>
            <col span="${len(consent_fields)}">
            <col span="${len(subsystem_fields)}" class="collapsible">
            <thead>
                <tr>
                    <th colspan="${len(consent_fields)}">
                        <div class="consents-metadata-header">
                            <div>
                                Consents Metadata
                            </div>
                            <div class="consents-metadata-button">
                                <input
                                    type="button"
                                    class="subsystem-display-button"
                                    value="Hide Subsystems Metadata <"
                                    onclick="toggleButtonColumns(this);"
                                />
                            </div>
                        </div>
                    </th>
                    <th colspan="${len(subsystem_fields)}" class="collapsible">
                        Subsystems Metadata
                    </th>
                </tr>
                <tr>
                    %for field in consent_fields:
                        <th>${consent_fields[field]}</th>
                    %endfor
                    %for field in subsystem_fields:
                        <th class="collapsible">${subsystem_fields[field]}</th>
                    %endfor
                </tr>
            </thead>
            <tbody>
            %for consent in consents:
                <%
                    subsystems = consent.get("subsystems") or []
                    colspan = len(subsystem_fields)
                    rowspan = len(subsystems) or 1
                %>
                <tr>
                    %for field in consent_fields:
                        <td rowspan="${rowspan}" class="consents-metadata">
                            ${utils.get_styled_value(consent[field], field)}
                        </td>
                    %endfor
                    %if len(subsystems) > 0:
                        ${render_subsystem(subsystems[0])}
                    %else:
                        <td colspan="${colspan}" class="collapsible">${utils.get_styled_value(None)}</td>
                    %endif
                </tr>
                %if len(subsystems) > 1:
                    %for i in range(1, len(subsystems)):
                        <tr>
                            ${render_subsystem(subsystems[i])}
                        </tr>
                    %endfor
                %endif
            %endfor
            </tbody>
        </table>
    </div>
    <div class="consents-history">
        <table>
            <thead>
                <tr>
                    <th>Changes</th>
                </tr>
            </thead>
            <tbody>
                %for change in changes:
                    <tr>
                        <td>${utils.get_styled_change(change)}</td>
                    </tr>
                %endfor
            </tbody>
        </table>
    </div>
</div>
