#include<bits/stdc++.h>
using namespace std;
const int MAXN=1e5+5;

int n,n_t,m;
int ts[MAXN];
string G_loc,out_loc;
auto seed = std::chrono::high_resolution_clock::now()
                .time_since_epoch()
                .count();
std::mt19937 rng(static_cast<unsigned>(seed));

void rd_suffle(int ts[],int n)
{
    for(int i = n; i >= 2; i--){
        swap(ts[n-1],ts[rng()%n]);
    }
    return;
}
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
        int _;
        cin>>c>>_;
        if(c=='t') ts[++n_t]=i;
    }
    rd_suffle(ts+1,n);
    for(int i=1;i<=n_t;i++)
    {
        cout<<ts[i]<<' ';
    }
    cout<<endl;
}