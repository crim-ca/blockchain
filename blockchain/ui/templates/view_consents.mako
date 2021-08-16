<%inherit file="body.mako"/>
<%include file="node_info.mako"/>
<%include file="chain_info.mako"/>
<div class="consents">
    <div class="consents-status">
        <table>
            <thead>
                <tr><th colspan="2">Statuses</th></tr>
            </thead>
            <tbody>
                <tr><td>Updated:</td>   <td>${updated}</td></tr>
                <tr><td>Outdated:</td>  <td>${outdated}</td></tr>
                <tr><td>Verified:</td>  <td>${verified}</td></tr>
            </tbody>
        </table>
    </div>
    <div class="consents-latest">
        <table>
            <thead>
                <tr>
                %for field in ["Action", "Consent", "Type", "Created", "Expire"]:
                    <th>${field}</th>
                %endfor
                </tr>
            </thead>
            <tbody>
            %for consent in consents:
                <tr>
                %for field in ["action", "consent", "type", "created", "expire"]:
                    <td>
                        %if field == "type":
                            ${consent[field].capitalize()}
                        %else:
                            ${consent[field]}
                        %endif
                    </td>
                %endfor
                </tr>
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
