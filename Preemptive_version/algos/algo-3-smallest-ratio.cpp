//根据当前 通讯节点比特数 与 “当前节点后继的计算节点所需时间的总和” 的比值，从小到大排序
#include<bits/stdc++.h>
using namespace std;
const int MAXN=1e5+5;

int n,n_t,m;
pair<double,int> a[MAXN];
int type[MAXN];
int weight[MAXN];
int out[MAXN];
int ans[MAXN];
vector<int> pre[MAXN];

queue<int> q;
string G_loc,out_loc;

int main(int argc,char* argv[])
{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
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
        if(type[v] == 0)
        {
            out[u]+=weight[v];
        }
        pre[v].push_back(u);
    }
    for(int i=1;i<=n;i++)
    {
        if(type[i]==1)
            a[++n_t]={((out[i]!=0)?1.0*weight[i]/out[i]:(1e9+7)),i};
    }
    sort(a+1,a+n_t+1);
    for(int i=1;i<=n_t;i++)
        cout<<a[i].second<<" ";
}