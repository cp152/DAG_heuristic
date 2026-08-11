#include<bits/stdc++.h>
using namespace std;
const int MAXN=1e5+5;

int n,n_t,m;
int ts[MAXN];
string G_loc,out_loc;

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
        int _;
        cin>>c>>_;
        if(c=='t') ts[++n_t]=i;
    }
    //输出 ts 的全排列
    do
    {
        for(int i=1;i<=n_t;i++)
            cout<<ts[i]<<" ";
        cout<<endl;
    } while(next_permutation(ts+1,ts+n_t+1));
}