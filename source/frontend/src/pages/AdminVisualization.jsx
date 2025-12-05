import { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import { FileText, Users, Folder, X, ChevronRight } from 'lucide-react';

export default function AdminVisualization() {
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE}/admin/dashboard`);
      const data = await response.json();
      setDashboard(data);
      buildMindMap(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      setLoading(false);
    }
  };

  const buildMindMap = (data) => {
    const newNodes = [];
    const newEdges = [];

    // Root node - All Stakeholders
    const rootNode = {
      id: 'root',
      type: 'default',
      data: { 
        label: (
          <div className="flex items-center gap-2 px-4 py-3">
            <Users size={24} className="text-blue-500" />
            <div>
              <div className="font-bold text-lg">All Roles</div>
              <div className="text-xs text-slate-500">{data.roles?.length || 0} roles</div>
            </div>
          </div>
        )
      },
      position: { x: 400, y: 50 },
      style: {
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        border: 'none',
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
        width: 250,
        fontSize: '16px',
        fontWeight: 'bold'
      }
    };
    newNodes.push(rootNode);

    // Role nodes
    const angleStep = (2 * Math.PI) / (data.roles?.length || 1);
    const radius = 350;

    data.roles?.forEach((role, index) => {
      const angle = index * angleStep;
      const x = 400 + radius * Math.cos(angle);
      const y = 300 + radius * Math.sin(angle);

      const roleDocuments = data.all_documents?.filter(doc => doc.role_id === role.id) || [];
      
      const roleNode = {
        id: `role-${role.id}`,
        type: 'default',
        data: { 
          label: (
            <div className="px-3 py-2">
              <div className="font-semibold text-sm">{role.role_name}</div>
              <div className="text-xs text-slate-500">{role.department}</div>
              <div className="text-xs text-blue-600 mt-1">{roleDocuments.length} documents</div>
            </div>
          ),
          roleData: role,
          documents: roleDocuments
        },
        position: { x, y },
        style: {
          background: 'white',
          border: '2px solid #3b82f6',
          borderRadius: '10px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          width: 180,
          cursor: 'pointer'
        }
      };
      newNodes.push(roleNode);

      // Edge from root to role
      newEdges.push({
        id: `edge-root-${role.id}`,
        source: 'root',
        target: `role-${role.id}`,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#3b82f6', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#3b82f6'
        }
      });

      // Document nodes for this role
      roleDocuments.forEach((doc, docIndex) => {
        const docAngle = angle + (docIndex - roleDocuments.length / 2) * 0.3;
        const docRadius = radius + 200;
        const docX = 400 + docRadius * Math.cos(docAngle);
        const docY = 300 + docRadius * Math.sin(docAngle);

        const docNode = {
          id: `doc-${doc.id}`,
          type: 'default',
          data: { 
            label: (
              <div className="px-2 py-1">
                <div className="flex items-center gap-1">
                  <FileText size={14} className="text-green-500" />
                  <div className="text-xs font-medium truncate" style={{ maxWidth: '120px' }}>
                    {doc.document_name}
                  </div>
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  {doc.confidence ? `${(doc.confidence * 100).toFixed(0)}%` : 'N/A'}
                </div>
              </div>
            ),
            documentData: doc
          },
          position: { x: docX, y: docY },
          style: {
            background: '#f0fdf4',
            border: '1.5px solid #22c55e',
            borderRadius: '8px',
            boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
            width: 140,
            fontSize: '12px',
            cursor: 'pointer'
          }
        };
        newNodes.push(docNode);

        // Edge from role to document
        newEdges.push({
          id: `edge-${role.id}-${doc.id}`,
          source: `role-${role.id}`,
          target: `doc-${doc.id}`,
          type: 'smoothstep',
          style: { stroke: '#22c55e', strokeWidth: 1 },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#22c55e'
          }
        });
      });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  };

  const onNodeClick = useCallback((event, node) => {
    if (node.id === 'root') {
      setSelectedNode({
        type: 'root',
        data: dashboard
      });
    } else if (node.id.startsWith('role-')) {
      setSelectedNode({
        type: 'role',
        data: node.data.roleData,
        documents: node.data.documents
      });
    } else if (node.id.startsWith('doc-')) {
      setSelectedNode({
        type: 'document',
        data: node.data.documentData
      });
    }
    setSidebarOpen(true);
  }, [dashboard]);

  const closeSidebar = () => {
    setSidebarOpen(false);
    setSelectedNode(null);
  };

  const getConfidenceBadge = (confidence) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-[calc(100vh-4rem)]">
      {/* Mind Map */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        attributionPosition="bottom-right"
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            if (node.id === 'root') return '#667eea';
            if (node.id.startsWith('role-')) return '#3b82f6';
            return '#22c55e';
          }}
          style={{
            backgroundColor: '#f8fafc'
          }}
        />
        <Panel position="top-left" className="bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-4">
          <h2 className="text-lg font-bold text-slate-900">Document Mind Map</h2>
          <p className="text-sm text-slate-600 mt-1">Click on nodes to view details</p>
          <div className="flex gap-4 mt-3 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-gradient-to-r from-purple-500 to-purple-700"></div>
              <span>Root</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span>Roles</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span>Documents</span>
            </div>
          </div>
        </Panel>
      </ReactFlow>

      {/* Detail Sidebar */}
      {sidebarOpen && selectedNode && (
        <div className="absolute top-0 right-0 h-full w-96 bg-white shadow-2xl border-l border-slate-200 overflow-y-auto z-10">
          <div className="sticky top-0 bg-white border-b border-slate-200 p-4 flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900">
              {selectedNode.type === 'root' && 'System Overview'}
              {selectedNode.type === 'role' && 'Role Details'}
              {selectedNode.type === 'document' && 'Document Details'}
            </h3>
            <button
              onClick={closeSidebar}
              className="p-1 hover:bg-slate-100 rounded-lg transition"
            >
              <X size={20} />
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* Root Node Details */}
            {selectedNode.type === 'root' && (
              <>
                <div className="bg-gradient-to-br from-purple-50 to-blue-50 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-3">
                    <Users className="text-purple-600" size={24} />
                    <h4 className="font-semibold text-lg">All Roles</h4>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-white p-3 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {selectedNode.data.overview?.total_roles || 0}
                      </div>
                      <div className="text-xs text-slate-600">Total Roles</div>
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {selectedNode.data.overview?.total_documents || 0}
                      </div>
                      <div className="text-xs text-slate-600">Documents</div>
                    </div>
                  </div>
                </div>

                <div>
                  <h5 className="font-semibold text-slate-700 mb-3">All Roles</h5>
                  <div className="space-y-2">
                    {selectedNode.data.roles?.map(role => (
                      <div key={role.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="font-medium text-slate-900">{role.role_name}</div>
                        <div className="text-xs text-slate-500">{role.department}</div>
                        <div className="text-xs text-blue-600 mt-1">
                          {role.document_count} documents
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Role Node Details */}
            {selectedNode.type === 'role' && (
              <>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Folder className="text-blue-600" size={24} />
                    <h4 className="font-semibold text-lg">{selectedNode.data.role_name}</h4>
                  </div>
                  <div className="text-sm text-slate-700 mb-3">{selectedNode.data.department}</div>
                  <div className="bg-white p-3 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {selectedNode.documents?.length || 0}
                    </div>
                    <div className="text-xs text-slate-600">Assigned Documents</div>
                  </div>
                </div>

                <div>
                  <h5 className="font-semibold text-slate-700 mb-2">Responsibilities</h5>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    {selectedNode.data.responsibilities}
                  </p>
                </div>

                <div>
                  <h5 className="font-semibold text-slate-700 mb-3">Documents</h5>
                  {selectedNode.documents && selectedNode.documents.length > 0 ? (
                    <div className="space-y-3">
                      {selectedNode.documents.map((doc, idx) => (
                        <div key={idx} className="p-3 bg-green-50 rounded-lg border border-green-200">
                          <div className="flex items-start gap-2">
                            <FileText size={16} className="text-green-600 mt-0.5" />
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-sm text-slate-900 truncate">
                                {doc.document_name}
                              </div>
                              {doc.summary && (
                                <div className="text-xs text-slate-600 mt-1 line-clamp-2">
                                  {doc.summary}
                                </div>
                              )}
                              <div className="flex items-center gap-2 mt-2">
                                {doc.confidence && (
                                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getConfidenceBadge(doc.confidence)}`}>
                                    {getConfidenceLabel(doc.confidence)} ({(doc.confidence * 100).toFixed(0)}%)
                                  </span>
                                )}
                                {doc.page_number && (
                                  <span className="text-xs text-slate-500">
                                    Page {doc.page_number}{doc.total_pages ? `/${doc.total_pages}` : ''}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-slate-500 text-center py-4">
                      No documents assigned yet
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Document Node Details */}
            {selectedNode.type === 'document' && (
              <>
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-3">
                    <FileText className="text-green-600" size={24} />
                    <h4 className="font-semibold text-lg break-words">
                      {selectedNode.data.document_name}
                    </h4>
                  </div>
                  {selectedNode.data.confidence && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-600">Confidence</span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getConfidenceBadge(selectedNode.data.confidence)}`}>
                        {getConfidenceLabel(selectedNode.data.confidence)} ({(selectedNode.data.confidence * 100).toFixed(0)}%)
                      </span>
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <div>
                    <h5 className="font-semibold text-slate-700 mb-2">Assigned To</h5>
                    <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="font-medium text-slate-900">
                        {selectedNode.data.roles?.role_name || 'N/A'}
                      </div>
                      <div className="text-sm text-slate-600">
                        {selectedNode.data.roles?.department || 'N/A'}
                      </div>
                    </div>
                  </div>

                  {selectedNode.data.summary && (
                    <div>
                      <h5 className="font-semibold text-slate-700 mb-2">Summary</h5>
                      <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg">
                        {selectedNode.data.summary}
                      </p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-3">
                    {selectedNode.data.page_number && (
                      <div className="bg-slate-50 p-3 rounded-lg">
                        <div className="text-xs text-slate-500 mb-1">Page Number</div>
                        <div className="text-lg font-semibold text-slate-900">
                          {selectedNode.data.page_number}
                        </div>
                      </div>
                    )}
                    {selectedNode.data.total_pages && (
                      <div className="bg-slate-50 p-3 rounded-lg">
                        <div className="text-xs text-slate-500 mb-1">Total Pages</div>
                        <div className="text-lg font-semibold text-slate-900">
                          {selectedNode.data.total_pages}
                        </div>
                      </div>
                    )}
                  </div>

                  {selectedNode.data.routed_at && (
                    <div>
                      <h5 className="font-semibold text-slate-700 mb-2">Routed At</h5>
                      <div className="text-sm text-slate-600">
                        {new Date(selectedNode.data.routed_at).toLocaleString()}
                      </div>
                    </div>
                  )}

                  {selectedNode.data.metadata && (
                    <div>
                      <h5 className="font-semibold text-slate-700 mb-2">Additional Info</h5>
                      <div className="bg-slate-50 p-3 rounded-lg">
                        {selectedNode.data.metadata.fallback_used !== undefined && (
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-slate-600">Fallback Used</span>
                            <span className="font-medium">
                              {selectedNode.data.metadata.fallback_used ? 'Yes' : 'No'}
                            </span>
                          </div>
                        )}
                        {selectedNode.data.metadata.confidence_level && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600">Confidence Level</span>
                            <span className="font-medium capitalize">
                              {selectedNode.data.metadata.confidence_level}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
