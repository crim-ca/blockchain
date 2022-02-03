<%inherit file="body.mako"/>
<%include file="node_info.mako"/>
<%include file="chain_info.mako"/>
<%namespace name="utils" file="utils.mako"/>

<script>
    function hideColumn(columns) {
            columns.forEach(function(num, i) {
                columns[i] = "#col_" + columns[i];
            });
            let selectors = columns.join(", ");
        // reset previously hidden
            let hidden = document.querySelectorAll(".collapsed-col");
            hidden.forEach(function(el) {
            el.classList.remove("collapsed-col");
        });
        // hide cells by class
            let cells = document.querySelectorAll(selectors);
            cells.forEach(function(item, i) {
            item.classList.add("collapsed-col");
        });
    }
</script>

<div class="consents">
    <div class="consents-status">
        <table>
            <thead>
                <tr><th colspan="2">Statuses</th></tr>
            </thead>
            <tbody>
                <tr><td>Updated:</td>   <td>${utils.get_styled_value(updated, "updated-datetime")}</td></tr>
                <tr><td>Outdated:</td>  <td>${utils.get_styled_value(outdated, "outdated-status")}</td></tr>
                <tr><td>Verified:</td>  <td>${utils.get_styled_value(verified, "verified-status")}</td></tr>
            </tbody>
        </table>
    </div>
    <div class="consents-latest">
        <table>
            <col span="${len(consent_fields)}" id="col-consent-meta">
            <col span="${len(subsystem_fields)}" id="col-subsystems">
            <thead>
                <tr>
                    <th colspan="${len(consent_fields)}">
                        Consents Metadata
                    </th>
                    <th colspan="${len(subsystem_fields)}">
                        Subsystems Metadata
                    </th>
                </tr>
                <tr>
                    %for field in consent_fields:
                        <th>${consent_fields[field]}</th>
                    %endfor
                    %for field in subsystem_fields:
                        <th>${subsystem_fields[field]}</th>
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
                        <td colspan="${colspan}"> </td>
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
                        <td>${change}</td>
                    </tr>
                %endfor
            </tbody>
        </table>
    </div>
</div>

<%def name="render_subsystem(subsystem)">
    <td>
        %for field in subsystem_fields:
            ${utils.get_styled_value(subsystem.get(field), field)}
        %endfor
    </td>
</%def>
