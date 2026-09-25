import { useQuery } from "@tanstack/react-query";
import PageHeader from "../components/PageHeader";
import { LoadingState, ErrorState, EmptyState } from "../components/States";
import { listUsers, listBusinessFunctions, listCapabilities } from "../services/lookups";

export default function AdminUsers() {
  const { data: users, isLoading, isError } = useQuery({ queryKey: ["users", "all"], queryFn: () => listUsers() });
  const { data: businessFunctions } = useQuery({ queryKey: ["business-functions"], queryFn: listBusinessFunctions });
  const { data: capabilities } = useQuery({ queryKey: ["capabilities"], queryFn: listCapabilities });

  return (
    <>
      <PageHeader title="Admin — Users & Reference Data" />
      <div className="content grid-2">
        <div className="card">
          <div className="card-pad" style={{ paddingBottom: 0 }}>
            <p className="section-title">Users</p>
          </div>
          {isLoading ? (
            <LoadingState />
          ) : isError ? (
            <ErrorState />
          ) : !users?.length ? (
            <EmptyState title="No users found" />
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Business Function</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} style={{ cursor: "default" }}>
                    <td>{u.name}</td>
                    <td className="muted">{u.email}</td>
                    <td>{u.role.replace("_", " ")}</td>
                    <td>{u.business_function || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="stack">
          <div className="card card-pad">
            <p className="section-title">Business Functions</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {businessFunctions?.map((bf) => (
                <span key={bf.id} className="chip chip-neutral">
                  {bf.name}
                </span>
              ))}
            </div>
          </div>
          <div className="card card-pad">
            <p className="section-title">Capabilities</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {capabilities?.map((c) => (
                <span key={c.id} className="chip chip-primary">
                  {c.name}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
