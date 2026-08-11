//根据 当前节点及其后续所有节点中 传输节点总比特数 和 计算节点总耗时 的比值，从小到大排序
#include<bits/stdc++.h>
using namespace std;
const int MAXN=1e5+5;

int n,n_t,m;
pair<double,int> a[MAXN];
int type[MAXN];
int weight[MAXN];
int sc[MAXN];
int st[MAXN];
int cnt[MAXN];
vector<int> adj[MAXN];

queue<int> q;
string G_loc,out_loc;

void dfs(int u,int root)
{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    if(cnt[u]==root) return;
    cnt[u] = root;
    if(type[u]==1)
    {
        st[root]+=weight[u];
    }
    else
    {
        sc[root]+=weight[u];
    }
    for(int v:adj[u])
    {
        if(v==root) continue;
        if(cnt[v]!=root)
            dfs(v,root);
    }
    return;
}

int main(int argc,char* argv[])
{
    if(argc<3)
    {
        cerr<<"Usage: "<<argv[0]<<" <G_file> <output_file>"<<endl;
        return 1;
    }
    G_loc=argv[1];
    out_loc=argv[2];
    freopen(G_loc.c_str(),"r",stdin);
    freopen(out_loc.c_str(),"w",stdout);

    cin>>n>>m;
    for(int i=1;i<=n;i++)
    {
        char c;
        cin>>c>>weight[i];
        type[i]=(c=='c'?0:1);
    }
    for(int i=1;i<=m;i++)
    {
        int u,v;
        cin>>u>>v;
        adj[u].push_back(v);
    }
    for(int i=1;i<=n;i++)
    {
        if(type[i]==1)
        {
            dfs(i,i);
            a[++n_t]={((sc[i]!=0)?1.0*st[i]/sc[i]:(1e9+7)),i};
        }
    }
    sort(a+1,a+n_t+1);
    for(int i=1;i<=n_t;i++)
        cout<<a[i].second<<" ";
}